from ztest.core import Cmd
from utils.error import ZTestError
import os
import tempfile
from utils import defer, bash
import ignite
import docker
from ztest import config

KERNEL_TAG = 'ztest:kernel-4.19.125'
SANDBOX_IMAGE_TAG = 'weaveworks/ignite:v0.8.0'


def init_check():
    if config.CONFIG.conf.kernel_tag is None:
        raise ZTestError('kernel image is not found, run "ztest init" first')

    if config.CONFIG.conf.image_tag is None:
        raise ZTestError('default image is not found, run "ztest init" first, or run "ztest import -d" to import a default image,'
                         'or run "ztest set-default-image to set a default image"')


class InitCmd(Cmd):
    def __init__(self):
        super(InitCmd, self).__init__(
            name='init',
            help='initialize ztest environment',
            args=[
                (['-t', '--tar'], {'help': 'path to the tar.gz which contains init binaries', 'dest': 'tar', 'required': True}),
                (['-k', '--kernel-tag'], {'help': 'the tag of kernel image', 'dest': 'kernel', 'required': False, 'default': None})
            ]
        )

        self.tar = None

    @defer.protect
    def _run(self, args, extra=None):
        self.tar = args.tar
        self.kernel_tag = args.kernel

        if self.kernel_tag is None:
            self.kernel_tag = KERNEL_TAG

        if not os.path.isfile(self.tar):
            raise ZTestError('cannot find the tarball %s' % self.tar)

        base_dir = tempfile.mkdtemp()
        defer.defer(lambda : bash.call_with_screen_output('rm -rf %s' % base_dir))

        bash.call_with_screen_output('tar xzf %s -C %s' % (self.tar, base_dir))

        wrapper_dir = os.path.join(base_dir, 'sandbox')
        if not os.path.isdir(wrapper_dir):
            raise ZTestError('tar file[%s] not containing sandbox/ directory' % self.tar)

        wrapper_files = os.listdir(wrapper_dir)
        if len(wrapper_files) == 0:
            raise ZTestError("tar file[%s]'s sandbox/ directory contains no file" % self.tar)

        if len(wrapper_files) > 1:
            raise ZTestError("tar file[%s]'s sandbox/ directory contains more than one files%s" % (self.tar, wrapper_files))

        wrapper_container_image = os.path.join(wrapper_dir, wrapper_files[0])

        kernel_dir = os.path.join(base_dir, 'kernel')
        if not os.path.isdir(kernel_dir):
            raise ZTestError('tar file[%s] not containing kernel/ directory' % self.tar)

        kernel_files = os.listdir(kernel_dir)
        if len(kernel_files) == 0:
            raise ZTestError("tar file[%s]'s kernel/ directory contains no file" % self.tar)

        if len(kernel_files) > 1:
            raise ZTestError("tar file[%s]'s kernel/ directory contains more than one files%s" % (self.tar, kernel_files))

        kernel = os.path.join(kernel_dir, kernel_files[0])

        wrapper_existed = False
        images = ignite.list_all_images()
        for img in images:
            if img.metadata.name == SANDBOX_IMAGE_TAG:
                wrapper_existed = True
                break

        kernel_existed = False
        for k in ignite.list_all_kernels():
            if k.metadata.name == self.kernel_tag:
                kernel_existed = True
                break

        if not wrapper_existed:
            wi = docker.import_image(wrapper_container_image)
            tag = '%s:%s' % (wi.Repository, wi.Tag)
            ignite.import_image(tag)

            config.CONFIG.set_sandbox_tag(tag)
            self.info('\n\nSUCCESSFULLY imported ignite sandbox image: %s' % tag)
        else:
            self.info('ignite wrapper image: %s existed, skip importing' % SANDBOX_IMAGE_TAG)

        if not kernel_existed:
            bash.call_with_screen_output('cat %s | docker import - %s' % (kernel, self.kernel_tag))
            ignite.import_kernel(self.kernel_tag)

            config.CONFIG.set_kernel_tag(self.kernel_tag)
            self.info('\n\nSUCCESSFULLY imported kernel image: %s' % self.kernel_tag)
        else:
            self.info('kernel image: %s existed, skip importing' % self.kernel_tag)
