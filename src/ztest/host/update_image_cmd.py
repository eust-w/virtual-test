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
                (['--existing-image-tag'], {'help': 'the tag of image to be updated', 'dest': 'existing_image_tag', 'required': True}),
                (['--new-image-tag'], {'help': 'the tag of new image', 'dest': 'new_tag', 'required': True}),
                (['--dockerfile'], {'help': 'the path of dockerfile', 'dest': 'dockerfile', 'default': None}),
                (['--ztest-pkg'], {'help': 'the path to ztest python package', 'dest': 'ztest_pkg', 'default': None}),
                (['--test-source'], {'help': 'the path to the test source', 'dest': 'test_source', 'default': None})
            ]
        )

        self.existing_image_tag = None
        self.new_tag = None
        self.dockerfile = None
        self.ztest_pkg = None
        self.test_source = None

    def _run(self, args, extra=None):
        if not docker.find_image(args.existing_image_tag):
            raise ZTestError('cannot find any image with tag[%s]' % args.existing_image_tag)

        if args.dockerfile is None and args.ztest_pkg is None:
            raise ZTestError('you need to specify either --dockerfile or --ztest-pkg to update the image')

        if docker.find_image(args.new_tag) is not None:
            docker.rm_old_docker_image(args.new_tag)

        self.existing_image_tag = args.existing_image_tag
        self.new_tag = args.new_tag
        self.dockerfile = args.dockerfile
        self.ztest_pkg = args.ztest_pkg
        self.test_source = args.test_source

        if any([self.ztest_pkg, self.test_source]):
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

        docker.commit(container_id, self.new_tag)
        docker.kill_containers([container_id])
        docker.rm_containers([container_id])
