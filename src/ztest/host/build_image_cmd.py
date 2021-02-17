import os

from utils import ZTestError
from utils import bash
from ztest.core import Cmd
from ztest import env
import cleanup_cmd
import docker
from jinja2 import Template
import ignite
from ztest import config

DOCKER_IMAGE_TEST_SOURCE_EXCLUDED = env.env_var('ztest.docker.baseImage.testSourceExcluded', str, '.git,dist')
DOCKER_IMAGE_TAG = env.env_var('ztest.docker.baseImage.tag', str, 'ztest:latest')


class BuildImageCmd(Cmd):
    def __init__(self):
        super(BuildImageCmd, self).__init__(
            name='build-image',
            help='build docker/ignite image',
            args=[
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

    def _cleanup_old_docker_image(self):
        docker.rm_old_docker_image(self.tag)

    def _copy_source_to_tmpdir(self, build_root):
        paths = [p for p in self.test_src.split('/') if p.strip()]
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
            bash.call_with_screen_output('rsync -a %s %s %s' % (' '.join(ignored), self.test_src, tmp_source))
        else:
            bash.call_with_screen_output('rsync -a %s %s' % (self.test_src, tmp_source))

        return os.path.basename(tmp_source), source_dir_name

    def _build_docker_image(self):
        build_root = os.path.abspath('tmp-%s' % os.path.basename(self.docker_build_src))
        bash.call_with_screen_output('rm -rf %s' % build_root)
        bash.call_with_screen_output('cp -r %s %s' % (self.docker_build_src, build_root))
        bash.call_with_screen_output('cp %s %s' % (self.ztest_pkg, build_root))

        docker_file = os.path.join(build_root, 'Dockerfile')
        if not os.path.isfile(docker_file):
            raise ZTestError('Dockerfile not found in: %s' % build_root)

        ztest_pkg_name = os.path.basename(self.ztest_pkg)

        source_path, source_dir_name = self._copy_source_to_tmpdir(build_root)
        with open(docker_file, 'r') as fd:
            content = fd.read()
            tmpt = Template(content)
            content = tmpt.render({
                'ztest_pkg_path': ztest_pkg_name,
                'ztest_pkg': ztest_pkg_name,
                'test_source_path': source_path,
                'test_source_name': source_dir_name
            })

        with open(docker_file, 'w+') as fd:
            fd.write(content)

        bash.call_with_screen_output('docker build -t %s .' % self.tag, work_dir=build_root)

    def _run(self, args, extra=None):
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
            ignite.import_image(self.tag)
            config.CONFIG.set_image_tag(self.tag)

        self.info('\nSUCCESSFULLY build image in ignite: %s. run "ignite image ls" could see it' % self.tag)

