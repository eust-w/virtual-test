import os
import socket

import psutil
from jinja2 import Template

import cleanup_cmd
import docker
import ignite
from utils import ZTestError
from utils import bash, misc
from ztest import config
from ztest import env
from ztest.core import Cmd

_excluded_source_dirs = [
    '.git',
    'dist',
    'venv',
    'agentcli',
    'apibinding',
    'appbuildsystem',
    'buildsystem',
    'installation',
    'setting',
    'zstackbuild',
    'zstackcli',
    'zstackctl',
    'bm-instance-agent',
    '*.pyc'
]

DOCKER_IMAGE_TEST_SOURCE_EXCLUDED = env.env_var('ZTEST_DOCKER_BASE_IMAGE_TEST_SOURCE_EXCLUDED', str, ','.join(_excluded_source_dirs))
DOCKER_IMAGE_TAG = env.env_var('ZTEST_DOCKER_BASE_IMAGE_TAG', str, 'ztest:latest')


def copy_source_to_tmpdir(test_src, build_root):
    paths = [p for p in test_src.split('/') if p.strip()]
    if len(paths) == 1:
        source_dir_name = paths[0]
    else:
        source_dir_name = paths[-1]

    tmp_source = os.path.join(build_root, 'tmp-%s' % source_dir_name)
    bash.call('rm -rf %s' % tmp_source)

    ignored = DOCKER_IMAGE_TEST_SOURCE_EXCLUDED.value().split(',')
    ignored = [i.strip() for i in ignored]
    ignored = ['--exclude "%s"' % i for i in ignored]

    if ignored:
        bash.call_with_screen_output('rsync -a %s %s %s' % (' '.join(ignored), test_src, tmp_source))
    else:
        bash.call_with_screen_output('rsync -a %s %s' % (test_src, tmp_source))

    return os.path.basename(tmp_source), source_dir_name


class BuildImageCmd(Cmd):
    def __init__(self):
        super(BuildImageCmd, self).__init__(
            name='build-image',
            help='build docker/ignite image',
            args=[
                (['--iso'], {'help': 'ISO path to ZStack ISO', 'dest': 'iso', 'required': True}),
                (['--only-docker'], {'help': 'only build docker image', 'action': 'store_true', 'dest': 'only_docker', 'default': False}),
                (['--docker-build-src'], {'help': 'the folder containing DockerBuild file', 'dest': 'docker_build_src', 'default': None}),
                (['--ztest-pkg'], {'help': 'ZTest python package file', 'dest': 'ztest_pkg', 'required': True}),
                (['--test-src'], {'help': 'source directory that includes code to be tested', 'dest': 'test_src', 'required': True}),
                (['--tag'], {'help': 'the tag for image in docker registry, e.g. ztest:latest', 'dest': 'tag', 'default': DOCKER_IMAGE_TAG.value()}),
                (['--use-existing'], {'help': 'used existing docker image with tag', 'dest': 'use_existing', 'action': 'store_true', 'default': False})
            ]
        )

        self.docker_build_root = None
        self.ztest_pkg = None
        self.test_src = None
        self.tag = None
        self.iso = None

    def _cleanup_old_docker_image(self):
        docker.rm_old_docker_image(self.tag)

    def _cleanup_yum_http_server(self):
        for p in psutil.process_iter():
            cmdline = p.cmdline()
            if 'python' in cmdline and 'SimpleHTTPServer' in cmdline:
                bash.call_with_screen_output('kill -9 %s' % p.pid)

    def _start_yum_http_server(self, ip, iso_dir):
        self._cleanup_yum_http_server()

        bash.call_with_screen_output('python -m SimpleHTTPServer &', work_dir=iso_dir)

        @misc.retry(time_out=5)
        def wait_for_yum_server_start():
            so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            so.settimeout(1)  # 1s
            so.connect((ip, 8000))

        wait_for_yum_server_start()

        return self._cleanup_yum_http_server

    def _setup_yum_server_and_prepare_repo(self, build_root):
        iso_dir = os.path.abspath('tmp-zstack-iso')

        if os.path.isdir(iso_dir):
            self._cleanup_yum_http_server()
            # try umount the iso_dir, ignore any error
            bash.call_with_screen_output('umount %s' % iso_dir, raise_error=False)
        else:
            os.makedirs(iso_dir)

        docker_host_ip = docker.get_host_ip_of_docker_bridge()
        bash.call_with_screen_output('mount %s %s' % (self.iso, iso_dir))
        cleanup_http_server = self._start_yum_http_server(docker_host_ip, iso_dir)

        # re-write repo files with yum server ip
        repo_dir = os.path.join(build_root, 'repo')
        for f in os.listdir(repo_dir):
            f = os.path.join(repo_dir, f)
            with open(f, 'r+') as fd:
                content = fd.read()
                tmpt = Template(content)
                content = tmpt.render({
                    'ip_and_port': '%s:8000' % docker_host_ip
                })

                fd.seek(0)
                fd.write(content)

        def cleanup_func():
            cleanup_http_server()
            bash.call_with_screen_output('umount %s' % iso_dir)
            bash.call_with_screen_output('rm -rf %s' % iso_dir)

        return cleanup_func

    def _build_docker_image(self):
        build_root = os.path.abspath('tmp-%s' % os.path.basename(self.docker_build_src))
        bash.call_with_screen_output('rm -rf %s' % build_root)
        bash.call_with_screen_output('cp -r %s %s' % (self.docker_build_src, build_root))
        bash.call_with_screen_output('cp %s %s' % (self.ztest_pkg, build_root))

        cleanup_yum_prepare_func = self._setup_yum_server_and_prepare_repo(build_root)

        docker_file = os.path.join(build_root, 'Dockerfile')
        if not os.path.isfile(docker_file):
            raise ZTestError('Dockerfile not found in: %s' % build_root)

        ztest_pkg_name = os.path.basename(self.ztest_pkg)

        source_path, source_dir_name = copy_source_to_tmpdir(self.test_src, build_root)
        with open(docker_file, 'r+') as fd:
            content = fd.read()
            tmpt = Template(content)
            content = tmpt.render({
                'ztest_pkg_path': ztest_pkg_name,
                'ztest_pkg': ztest_pkg_name,
                'test_source_path': source_path,
                'test_source_name': source_dir_name
            })

            fd.seek(0)
            fd.write(content)

        bash.call_with_screen_output('docker build -t %s .' % self.tag, work_dir=build_root)
        cleanup_yum_prepare_func()

    def _run(self, args, extra=None):
        self.iso = os.path.abspath(args.iso)
        if not os.path.isfile(self.iso):
            raise ZTestError('cannot find ISO file: %s' % self.iso)

        self.docker_build_src = os.path.abspath(args.docker_build_src)
        if not self.docker_build_src:
            self.docker_build_src = os.path.abspath('docker_build')

        if not os.path.isdir(self.docker_build_src):
            raise ZTestError('cannot find docker build root: %s' % self.docker_build_src)

        self.ztest_pkg = os.path.abspath(args.ztest_pkg)
        if not os.path.isfile(self.ztest_pkg):
            raise ZTestError('cannot find ztest python package: %s' % self.ztest_pkg)

        self.test_src = os.path.abspath(args.test_src)
        if not os.path.isdir(self.test_src):
            raise ZTestError('cannot find test source: %s' % self.test_src)

        self.tag = args.tag
        if not self.tag:
            self.tag = DOCKER_IMAGE_TAG.value()

        cleanup = cleanup_cmd.CleanupCmd()
        cleanup.run(None, None)

        if not args.use_existing:
            self._cleanup_old_docker_image()
            self._build_docker_image()

        if not docker.find_image(self.tag):
            raise ZTestError('not docker image with tag[%s] found, run "docker image ls" to check' % self.tag)

        if not args.only_docker:
            ignite.rm_image(self.tag)
            ignite.import_image(self.tag)
            config.CONFIG.set_image_tag(self.tag)

        self.info('\nSUCCESSFULLY build image in ignite: %s. run "ignite image ls" could see it' % self.tag)

