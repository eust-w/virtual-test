import os.path

import ignite
import sync_source
from utils.error import ZTestError
from ztest import env
from ztest.core import Cmd

SOURCE_DIR = env.env_var('ztest.source.dir', str, None)
TEST_IMAGE_TAG = env.env_var('ztest.image.tag', str, 'pyut:0.3')


class RunTest(Cmd):
    def __init__(self):
        super(RunTest, self).__init__(
            name='run-test',
            help='run a test case',
            prog='ztest run-test [options]',
            description='Example: ztest run-test --case zstack-utility/kvmagent/kvmagent/tests/test_start_vm.py',
            args=[
                (['--src'], {'help': 'path to root folder of source code', 'dest': 'src', 'required': True}),
                (['--image'], {'help': 'image tag name, e.g. pyut:0.3', 'dest': 'image', 'default': None})
            ]
        )

        self.vm_id = None
        self.image = None
        self.vm_name = None
        self.case_path = None
        self.source_root = None

    def _get_full_case_path(self, src_dir, case_file):
        pass

    def _run_vm(self):
        self.vm_id = ignite.run_vm(self.image, self.vm_name)

    def _sync_source(self):
        sync_source.sync_source_to_vm(self.vm_id, self.source_root)

    def _run(self, args, extra=None):
        if not args.src:
            args.src = SOURCE_DIR.value()

        src_root = os.path.split(args.src)[0]
        if not os.path.isdir(src_root):
            raise ZTestError('cannot find source root: %s' % src_root)

        self.source_root = src_root

        if not os.path.isfile(args.src):
            raise ZTestError('cannot find case: %s' % args.src)

        self.case_path = os.path.join(env.SOURCE_PARENT_DIR_IN_VM.value(), args.src)

        self.image = args.image
        if not self.image:
            self.image = TEST_IMAGE_TAG.value()

        self.vm_name = os.path.splitext(os.path.basename(args.src))[0].replace('_', '-')

        self._run_vm()
        self._sync_source()
