import os

import docker
from utils.error import ZTestError
from ztest import config
from ztest.core import Cmd
from ztest.host import ignite, cleanup_cmd


class ImportImageCmd(Cmd):
    def __init__(self):
        super(ImportImageCmd, self).__init__(
            name='import',
            help='import image',
            args=[
                (['-i', '--image'], {'help': 'path to the image tar.gz', 'dest': 'image', 'required': True}),
                (['-d', '--default'], {'help': 'set the image as the default image', 'dest': 'default', 'action': 'store_true', 'default': False})
            ]
        )

        self.image = None
        self.tag = None
        self.default = False

    def _cleanup_ignite(self):
        image = ignite.find_image(self.tag)
        if image is not None:
            cleanup_cmd.CleanupCmd().run(None, None)
            ignite.rm_image(image.metadata.uid)

    def _run(self, args, extra=None):
        self.image = args.image
        self.default = args.default

        if not os.path.isfile(self.image):
            raise ZTestError('cannot find image: %s' % self.image)

        img = docker.import_image(self.image)
        self.tag = '%s:%s' % (img.Repository, img.Tag)

        self._cleanup_ignite()
        ignite.import_image(self.tag)

        self.info('\n\nSUCCESSFULLY import image with tag %s' % self.tag)

        if self.default:
            config.CONFIG.set_image_tag(self.tag)
            self.info('The image is set as default image')


