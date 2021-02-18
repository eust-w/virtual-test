import os.path

import ignite
from utils.error import ZTestError
from utils import retry
from utils import bash
from ztest import env
from ztest.core import Cmd
from ztest import config
import build_image_cmd

SOURCE_DIR = env.env_var('ztest.source.dir', str, None)
TEST_IMAGE_TAG = env.env_var('ztest.image.tag', str, 'pyut:0.3')
WAIT_FOR_VM_SSD_TIMEOUT = env.env_var('ztest.vm.waitSshdTimeout', int, 30)
WAIT_FOR_VM_SSD_CHECK_INTERVAL = env.env_var('ztest.vm.checkSshdUpInterval', float, 0.5)
TEST_SOURCE_ROOT_FOLDER_NAME = env.env_var('ztest.source.rootFolderName', str, 'zstack-utility')


class CasePath(object):
    def __init__(self, case_path):
        self.case_path = case_path

        if not os.path.isfile(self.case_path):
            raise ZTestError('cannot find test case: %s' % self.case_path)

        ss = [s for s in self.case_path.split(os.sep) if s.strip(' \t\r')]
        try:
            root_folder_index = ss.index(TEST_SOURCE_ROOT_FOLDER_NAME.value())
        except ValueError:
            raise ZTestError('cannot find "%s" in path: %s' % (TEST_SOURCE_ROOT_FOLDER_NAME.value(), self.case_path))

        if os.path.isabs(case_path):
            p = [os.sep]
            p.extend(ss[:root_folder_index + 1])
            self.source_root = os.sep.join(p)
        else:
            self.source_root = os.sep.join(ss[:root_folder_index+1])

        if not os.path.isdir(self.source_root):
            raise ZTestError('cannot find source root: %s' % self.source_root)

        ss = ss[root_folder_index:]
        project_name = ss[1]

        self.case_path_in_vm = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), os.sep.join(ss[1:]))
        self.venv_path_in_vm = os.path.join(env.TEST_ENV_DIR_IN_VM.value(), project_name)
        self.zstacklib_path_in_vm = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), 'zstacklib')
        self.case_name = os.path.basename(case_path)


class RunTest(Cmd):
    def __init__(self):
        super(RunTest, self).__init__(
            name='test',
            help='run a test case',
            prog='ztest test [options]',
            description='Example: ztest test --case zstack-utility/kvmagent/kvmagent/tests/test_start_vm.py',
            args=[
                (['--case'], {'help': 'path to case file', 'dest': 'case_path', 'required': True}),
                (['--image'], {'help': 'image tag name, e.g. pyut:0.3', 'dest': 'image', 'default': None})
            ]
        )

        self.vm_id = None
        self.vm_ip = None
        self.image = None
        self.vm_name = None
        self.case_path = None  # type: CasePath

    def _run_vm(self):
        self.vm_id = ignite.run_vm(self.image, self.vm_name)
        self.vm_ip = ignite.get_vm_first_ip(self.vm_id)

    def _sync_source(self):
        ignored = build_image_cmd.DOCKER_IMAGE_TEST_SOURCE_EXCLUDED.value().split(',')
        ignored = ['--exclude "%s"' % i.strip() for i in ignored]
        if ignored:
            bash.call_with_screen_output(
                'rsync -avz %s -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
                (' '.join(ignored), env.SSH_PRIV_KEY_FILE.value(), self.case_path.source_root, self.vm_ip, env.SOURCE_PARENT_DIR_IN_VM.value()))
        else:
            bash.call_with_screen_output('rsync -avz -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
                (env.SSH_PRIV_KEY_FILE.value(), self.case_path.source_root, self.vm_ip, env.SOURCE_PARENT_DIR_IN_VM.value()))

    @retry(time_out=WAIT_FOR_VM_SSD_TIMEOUT.value(), check_interval=WAIT_FOR_VM_SSD_CHECK_INTERVAL.value())
    def _wait_for_vm_sshd(self):
        self.info('wait for VM[%s, %s] ssh start ...' % (self.vm_id, self.vm_ip))

        r, o, e = bash.run('ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s "echo 1"' % (env.SSH_PRIV_KEY_FILE.value(), self.vm_ip))

        if r != 0:
            raise ZTestError('unable to ssh into root@%s, %s' % (self.vm_ip, e))

    def _run(self, args, extra=None):
        self.case_path = CasePath(args.case_path)

        self.image = args.image
        if self.image is None:
            self.image = config.CONFIG.conf.image_tag

        self.vm_name = os.path.splitext(self.case_path.case_name)[0].replace('_', '-')

        self._run_vm()
        self._wait_for_vm_sshd()
        self._sync_source()
        self._run_test()

    def _run_test(self):
        ignite.bash_call_with_screen_output(
            self.vm_id,
            'zguest test --case %s --venv %s --zstacklib %s' % (self.case_path.case_path_in_vm, self.case_path.venv_path_in_vm, self.case_path.zstacklib_path_in_vm),
            env.SSH_PRIV_KEY_FILE.value()
        )

