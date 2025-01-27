import os

from ztest.core import Cmd
from utils.error import ZTestError
import docker
import ignite
from ztest import config
import cleanup_cmd
import build_image_cmd
from ztest import env
from utils import bash


class UpdateImageCmd(Cmd):
    def __init__(self):
        super(UpdateImageCmd, self).__init__(
            name='update-image',
            help='update an existing image by Dockerfile/ztest and produce a new image',
            args=[
                (['-t', '--tag'], {'help': 'the tag of image to be updated', 'dest': 'existing_image_tag', 'required': True}),
                (['-n', '--new-tag'], {'help': 'the tag of new image', 'dest': 'new_tag', 'default': None}),
                (['--dockerfile'], {'help': 'the path of dockerfile', 'dest': 'dockerfile', 'default': None}),
                (['-z', '--ztest-pkg'], {'help': 'the path to ztest python package', 'dest': 'ztest_pkg', 'default': None}),
                (['--test-source'], {'help': 'the path to the test source', 'dest': 'test_source', 'default': None}),
                (['--pip'], {'help': 'pip install packages, multiple packages split by comma, e.g. --pip flask,cherryPy', 'dest': 'pip', 'default': None}),
                (['--yum'], {'help': 'yum install packages, multiple packages split by comma, e.g. --yum gdb,gcc', 'dest': 'yum', 'default': None}),
                (['--venv'], {'help': 'update venv environment', 'action': 'store_true', 'default': False}),
                (['--run'], {'help': '[Support Multiple] run a single line command in the image, e.g. --run "echo hello > /root/greeting"', 'action': 'append', 'dest': 'run', 'default': None}),
                (['--cp'], {'help': '[Support Multiple] copy files/directories into the image, e.g. --cp "path_to_a_file_on_the_host path_in_the_image"', 'action': 'append', 'dest': 'cp', 'default': None})
            ]
        )

        self.existing_image_tag = None
        self.new_tag = None
        self.dockerfile = None
        self.ztest_pkg = None
        self.test_source = None
        self.pip = None
        self.update_venv = None
        self.yum = None
        self.run_cmd = None
        self.cp = None

    def _run(self, args, extra=None):
        self.existing_image_tag = args.existing_image_tag
        self.new_tag = args.new_tag
        self.dockerfile = args.dockerfile
        self.ztest_pkg = args.ztest_pkg
        self.test_source = args.test_source
        self.pip = args.pip
        self.update_venv = args.venv
        self.yum = args.yum
        self.run_cmd = args.run
        self.cp = args.cp

        if self.new_tag is None:
            self.new_tag = self.existing_image_tag

        if not docker.find_image(self.existing_image_tag):
            raise ZTestError('cannot find any image with tag[%s]' % self.existing_image_tag)

        partial = any([self.ztest_pkg, self.test_source, self.pip, self.update_venv, self.yum, self.run_cmd, self.cp])

        if self.dockerfile is None and not partial:
            raise ZTestError('you need to specify either --dockerfile or --ztest-pkg to update the image')

        if self.cp:
            for cp in self.cp:
                if len(cp.split()) != 2:
                    raise ZTestError('wrong option --cp %s, the format should be "source destination"' % cp)

        if partial:
            self._update_partial()
        elif self.dockerfile is not None:
            self._update_by_dockerfile()

        self._cleanup_ignite()
        ignite.import_image(self.new_tag)
        config.CONFIG.set_image_tag(self.new_tag)

        self.info('SUCCESSFULLY update image[%s] into ignite, use "ignite image ls" to check' % self.new_tag)

    def _cleanup_ignite(self):
        image = ignite.find_image(self.new_tag)
        if image is not None:
            cleanup_cmd.CleanupCmd().run(None, None)
            ignite.rm_image(image.metadata.uid)

    def _update_by_dockerfile(self):
        pass

    def _update_partial(self):
        if self.ztest_pkg and not os.path.isfile(self.ztest_pkg):
            raise ZTestError('cannot find ztest python package: %s' % self.ztest_pkg)
        if self.test_source and not os.path.isdir(self.test_source):
            raise ZTestError('cannot find test source: %s' % self.test_source)

        container_id = docker.run('-d %s' % self.existing_image_tag)

        if self.ztest_pkg:
            docker.cp_in(container_id, self.ztest_pkg, '/root')
            docker.bash_call_with_screen_output(container_id, 'pip install %s' % os.path.join(env.SOURCE_PARENT_DIR_IN_VM.value(), os.path.basename(self.ztest_pkg)))

        if self.test_source:
            tmp_src, src_dir_name = build_image_cmd.copy_source_to_tmpdir(self.test_source, '.')
            src_in_vm = os.path.join(env.SOURCE_PARENT_DIR_IN_VM.value(), src_dir_name)
            docker.bash_call_with_screen_output(container_id, 'rm -rf %s' % src_in_vm)
            docker.cp_in(container_id, '%s/.' % tmp_src, src_in_vm)
            bash.call_with_screen_output('rm -rf %s' % tmp_src)

        if self.pip:
            pkgs = self.pip.split(',')
            pkgs = [p.strip() for p in pkgs]
            docker.bash_call_with_screen_output(container_id, 'pip install %s' % ' '.join(pkgs))

        if self.yum:
            pkgs = self.yum.split(',')
            pkgs = [p.strip() for p in pkgs]
            docker.bash_call_with_screen_output(container_id, 'yum -y install %s' % ' '.join(pkgs))

        if self.update_venv:
            docker.bash_call_with_screen_output(container_id, 'zguest venv')

        if self.run_cmd:
            for cmd in self.run_cmd:
                docker.bash_call_with_screen_output(container_id, cmd)

        if self.cp:
            for cp in self.cp:
                src, dst = cp.split()
                docker.cp_in(container_id, src, dst)

        docker.commit(container_id, self.new_tag)
        docker.kill_containers([container_id])
        docker.rm_containers([container_id])
