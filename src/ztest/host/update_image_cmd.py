import os

from ztest.core import Cmd
from utils.error import ZTestError
import docker
import ignite
from ztest import config
import cleanup_cmd


class UpdateImageCmd(Cmd):
    def __init__(self):
        super(UpdateImageCmd, self).__init__(
            name='update-image',
            help='update an existing image by Dockerfile/ztest and produce a new image',
            args=[
                (['--existing-image-tag'], {'help': 'the tag of image to be updated', 'dest': 'existing_image_tag', 'required': True}),
                (['--new-image-tag'], {'help': 'the tag of new image', 'dest': 'new_tag', 'required': True}),
                (['--dockerfile'], {'help': 'the path of dockerfile', 'dest': 'dockerfile', 'default': None}),
                (['--ztest-pkg'], {'help': 'the path to ztest python package', 'dest': 'ztest_pkg', 'default': None})
            ]
        )

        self.existing_image_tag = None
        self.new_tag = None
        self.dockerfile = None
        self.ztest_pkg = None

    def _run(self, args, extra=None):
        if not docker.find_image(args.existing_image_tag):
            raise ZTestError('cannot find any image with tag[%s]' % args.existing_image_tag)

        if docker.find_image(args.new_tag):
            raise ZTestError('there is already an image with tag[%s]' % args.new_tag)

        if args.dockerfile is None and args.ztest_pkg is None:
            raise ZTestError('you need to specify either --dockerfile or --ztest-pkg to update the image')

        self.existing_image_tag = args.existing_image_tag
        self.new_tag = args.new_tag
        self.dockerfile = args.dockerfile
        self.ztest_pkg = args.ztest_pkg

        if self.ztest_pkg is not None:
            self._update_ztest_pkg()
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

    def _update_ztest_pkg(self):
        if not os.path.isfile(self.ztest_pkg):
            raise ZTestError('cannot find ztest python package: %s' % self.ztest_pkg)

        container_id = docker.run('-d %s' % self.existing_image_tag)
        docker.cp_in(container_id, self.ztest_pkg, '/root')
        docker.bash_call_with_screen_output(container_id, 'pip install %s' % os.path.join('/root', os.path.basename(self.ztest_pkg)))
        docker.commit(container_id, self.new_tag)
        docker.kill_containers([container_id])
        docker.rm_containers([container_id])
