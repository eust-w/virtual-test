import os.path

import ignite
from utils.error import ZTestError
from utils import retry
from utils import bash
from ztest import env
from ztest.core import Cmd
from ztest import config

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
                (['--case'], {'help': 'path to case file', 'dest': 'case_path', 'required': True}),
                (['--image'], {'help': 'image tag name, e.g. pyut:0.3', 'dest': 'image', 'default': None})
            ]
        )

        self.vm_id = None
        self.vm_ip = None
        self.image = None
        self.vm_name = None
        self.source_root = None
        self.case_path = None

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
        self.info('wait for VM[%s, %s] ssh start ...' % (self.vm_id, self.vm_ip))

        r, o, e = bash.run('ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s "echo 1"' % (env.SSH_PRIV_KEY_FILE.value(), self.vm_ip))

        if r != 0:
            raise ZTestError('unable to ssh into root@%s, %s' % (self.vm_ip, e))

    def _run(self, args, extra=None):
        self.case_path = args.case_path
        if not os.path.isfile(self.case_path):
            raise ZTestError('cannot find case: %s' % self.case_path)

        src_root = self.case_path.split(os.sep)[0]
        if not os.path.isdir(src_root):
            raise ZTestError('cannot find source root: %s' % src_root)

        self.source_root = src_root
        self.image = args.image
        if self.image is None:
            self.image = config.CONFIG.conf.image_tag

        self.vm_name = os.path.splitext(os.path.basename(self.case_path))[0].replace('_', '-')

        self._run_vm()
        self._wait_for_vm_sshd()
        self._sync_source()
        self._run_test()

    def _run_test(self):
        ss = self.case_path.split(os.sep)

        project_name = ss[2]
        case_path_in_vm = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), os.sep.join(ss[1:]))
        venv_path_in_vm = os.path.join(env.TEST_ENV_DIR_IN_VM.value(), project_name)
        zstacklib_path_in_vm = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), 'zstacklib')
        ignite.bash_call_with_screen_output(
            self.vm_id,
            'zguest test --case %s --venv %s --zstacklib %s' % (case_path_in_vm, venv_path_in_vm, zstacklib_path_in_vm),
            env.SSH_PRIV_KEY_FILE.value()
        )

