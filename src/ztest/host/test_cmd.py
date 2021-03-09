import os.path

import ignite
import setup_utils
import vm_utils
from utils import defer, json
from utils.error import ZTestError
from ztest import config
from ztest import env
from ztest.core import Cmd
from ztest.host.vm_utils import run_vm, wait_for_vm_sshd, sync_source

SOURCE_DIR = env.env_var('ZTEST_SOURCE_DIR', str, None)
TEST_SOURCE_ROOT_FOLDER_NAME = env.env_var('ZTEST_SOURCE_ROOT_FOLDER_NAME', str, 'zstack-utility')


class CasePath(object):
    def __init__(self, case_expression):
        # the param may like 'tests/my-directory/test_demo.py::TestClassName::test_specific_method'
        # which contains methods to test
        case_express = case_expression.split('::')
        case_path = case_express[0]
        self.case_file_path = case_path

        if not os.path.exists(case_path):
            raise ZTestError('cannot find test case: %s' % case_path)

        ss = [s for s in case_path.split(os.sep) if s.strip(' \t\r')]
        try:
            root_folder_index = ss.index(TEST_SOURCE_ROOT_FOLDER_NAME.value())
        except ValueError:
            raise ZTestError('cannot find "%s" in path: %s' % (TEST_SOURCE_ROOT_FOLDER_NAME.value(), case_path))

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

        self.case_expression_in_vm = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), os.sep.join(ss[1:]))
        if len(case_express) > 1:
            # there are :: expression, append them to the case_expression_in_vm
            ss = [self.case_expression_in_vm]
            ss.extend(case_express[1:])
            self.case_expression_in_vm = '::'.join(ss)

        self.venv_path_in_vm = os.path.join(env.TEST_ENV_DIR_IN_VM.value(), project_name)
        self.zstacklib_path_in_vm = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), 'zstacklib')
        self.case_name = os.path.basename(case_path)

        if os.path.isfile(case_path):
            self.vm_name = os.path.splitext(self.case_name)[0].replace('_', '-')
        else:
            self.vm_name = self.case_expression_in_vm.replace('/', '-').strip('-')


class RunTest(Cmd):
    def __init__(self):
        super(RunTest, self).__init__(
            name='test',
            help='run a test case',
            prog='ztest test [options]',
            description='Example: ztest test --case zstack-utility/kvmagent/kvmagent/tests/test_start_vm.py',
            args=[
                (['--case'], {'help': 'path to case file', 'dest': 'case_path', 'required': True}),
                (['--image'], {'help': 'image tag name, e.g. pyut:0.3', 'dest': 'image', 'default': None}),
                (['-k', '--kernel'], {'help': 'kernel for ignite starting vm,, run "ignite kernel ls" to check', 'dest': 'kernel', 'default': None}),
                (['-n', '--no-zstacklib'], {'help': 'not to update zstacklib when running the test', 'action': 'store_true', 'dest': 'no_zstacklib', 'default': False}),
                (['-f', '--fail-on-existing-vm'], {'help': 'if there is an existing vm with the same name the case uses, fail fast', 'dest': 'fail_on_existing_vm', 'action': 'store_true', 'default': False}),
                (['-ke', '--keep'], {'help': 'keep the vm after testing done', 'dest': 'keep', 'action': 'store_true', 'default': False}),
                (['-lo', '--log-dir'], {'help': 'if set, the test log will be put in the dir', 'dest': 'log_dir', 'default': None}),
                (['-dr', '--dry-run'], {'help': 'dry-run the cases to collect metedata', 'action': 'store_true', 'dest': 'dry_run', 'default': False})
            ]
        )

        self.vm_id = None
        self.vm_ip = None
        self.image = None
        self.vm_name = None
        self.case_path = None  # type: CasePath
        self.fail_on_existing_vm = False
        self.no_zstacklib = False
        self.kernel = None
        self.keep = None
        self.log_dir = None
        self.dry_run = False

    def _run_vm(self):
        self.vm_id, self.vm_ip = run_vm(self.vm_name, kernel=self.kernel, image=self.image, fail_on_existing_vm=self.fail_on_existing_vm)

    def _sync_source(self):
        sync_source(self.vm_ip, self.case_path.source_root)

    def _wait_for_vm_sshd(self):
        wait_for_vm_sshd(self.vm_id, self.vm_ip)

    def _run_setup(self):
        clean = setup_utils.run_setup(self.case_path.case_file_path)

        if not self.keep:
            defer.defer(clean)

    @defer.protect
    def _run(self, args, extra=None):
        self.case_path = CasePath(args.case_path)

        self.image = args.image
        if self.image is None:
            self.image = config.CONFIG.conf.image_tag

        self.vm_name = self.case_path.vm_name
        self.fail_on_existing_vm = args.fail_on_existing_vm
        self.no_zstacklib = args.no_zstacklib
        self.kernel = args.kernel
        self.keep = args.keep
        self.log_dir = args.log_dir
        self.dry_run = args.dry_run

        if self.log_dir is not None and not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)

        if self.kernel is None:
            self.kernel = config.CONFIG.conf.kernel_tag

        self._run_setup()
        self._run_vm()
        self._wait_for_vm_sshd()
        self._sync_source()
        self._run_test()
        self._cleanvm()

    def _cleanvm(self):
        if not self.keep:
            ignite.kill_vms([self.vm_id])
            ignite.rm_vms([self.vm_id])
        else:
            self.info('--keep is set, do not remove vm[%s, %s]' % (self.vm_id, self.vm_ip))

    def _set_vm_env_vars(self):
        test_env_metadata = {
            'ip': self.vm_id,
        }

        env.set_vm_env_var('ZTEST_ENV_METADATA', json.dumps(test_env_metadata))
        env.set_ssh_private_key_to_vm_env_vars()
        vm_utils.create_env_var_file_in_vm(self.vm_id)

    def _run_test(self):
        self._set_vm_env_vars()

        log_dir = self.log_dir if self.log_dir is not None else '.'
        log_file_path = os.path.join(log_dir, '%s.log' % self.vm_name)

        cmd_lst = ['zguest test --case %s --venv %s' % (self.case_path.case_expression_in_vm, self.case_path.venv_path_in_vm)]
        if not self.no_zstacklib:
            cmd_lst.append('--zstacklib %s' % self.case_path.zstacklib_path_in_vm)
        if self.dry_run:
            cmd_lst.append('--dry-run')

        ignite.bash_call_with_screen_output(
            self.vm_id,
            ' '.join(cmd_lst),
            env.SSH_PRIV_KEY_FILE.value(),
            log_file_path
        )

