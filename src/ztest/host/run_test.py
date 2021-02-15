import os.path

import ignite
from utils.error import ZTestError
from utils import retry
from utils import bash
from ztest import env
from ztest.core import Cmd

SOURCE_DIR = env.env_var('ztest.source.dir', str, None)
IGNORED_SOURCE = env.env_var('ztest.source.ignore', str, '.git,dist')
TEST_IMAGE_TAG = env.env_var('ztest.image.tag', str, 'pyut:0.3')
WAIT_FOR_VM_SSD_TIMEOUT = env.env_var('ztest.vm.waitSshdTimeout', int, 30)
WAIT_FOR_VM_SSD_CHECK_INTERVAL = env.env_var('ztest.vm.checkSshdUpInterval', float, 0.5)


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
        self.vm_ip = None
        self.image = None
        self.vm_name = None
        self.case_path = None
        self.source_root = None

    def _run_vm(self):
        self.vm_id = ignite.run_vm(self.image, self.vm_name)
        self.vm_ip = ignite.get_vm_first_ip(self.vm_id)

    def _sync_source(self):
        ignored = IGNORED_SOURCE.value().split(',')
        ignored = ['--exclude "%s"' % i.strip() for i in ignored]
        if ignored:
            bash.call_with_screen_output(
                'rsync -avz %s -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
                (' '.join(ignored), env.SSH_PRIV_KEY_FILE.value(), self.source_root, self.vm_ip, env.SOURCE_PARENT_DIR_IN_VM.value()))
        else:
            bash.call_with_screen_output('rsync -avz -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
                (env.SSH_PRIV_KEY_FILE.value(), self.source_root, self.vm_ip, env.SOURCE_PARENT_DIR_IN_VM.value()))

    @retry(time_out=WAIT_FOR_VM_SSD_TIMEOUT.value(), check_interval=WAIT_FOR_VM_SSD_CHECK_INTERVAL.value())
    def _wait_for_vm_sshd(self):
        r, o, e = bash.run('ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s "echo 1"' % (env.SSH_PRIV_KEY_FILE.value(), self.vm_ip))

        if r != 0:
            raise ZTestError('unable to ssh into root@%s, %s' % (self.vm_ip, e))

    def _run(self, args, extra=None):
        if not args.src:
            args.src = SOURCE_DIR.value()

        src_root = args.src.split(os.sep)[0]
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
        self._wait_for_vm_sshd()
        self._sync_source()
