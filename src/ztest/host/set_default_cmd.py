from ztest.core import Cmd
from utils.error import ZTestError
from ztest import config
import ignite


class SetDefaultCmd(Cmd):
    def __init__(self):
        super(SetDefaultCmd, self).__init__(
            name='set-default',
            help='set default kernel/image',
            args=[
                (['-i', '--image-tag'], {'help': 'tag of image', 'dest': 'image_tag', 'default': None, 'required': False}),
                (['-k', '--kernel-tag'], {'help': 'tag of kernel', 'dest': 'kernel_tag', 'default': None, 'required': False})
            ]
        )

        self.image = None
        self.kernel = None

    def _set_default_kernel(self):
        if self.kernel is None:
            return

        if ignite.find_kernel(self.kernel) is None:
            raise ZTestError('cannot find kernel[%s], run "ignite kernel ls" to check' % self.image)

        config.CONFIG.set_kernel_tag(self.kernel)
        self.info('SUCCESSFULLY set kernel[%s] as default kernel' % self.kernel)

    def _set_default_image(self):
        if self.image is None:
            return

        if ignite.find_image(self.image) is None:
            raise ZTestError('cannot find image[%s], run "ignite image ls" to check' % self.image)

        config.CONFIG.set_image_tag(self.image)

        self.info('SUCCESSFULLY set image[%s] as default image' % self.image)

    def _run(self, args, extra=None):
        self.image = args.image_tag
        self.kernel = args.kernel_tag

        self._set_default_image()
        self._set_default_kernel()


