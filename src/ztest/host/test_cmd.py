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
VM_KERNEL = env.env_var('ztest.vm.kernel', str, 'ztest:kernel-4.19.125')


class CasePath(object):
    def __init__(self, case_expression):
        # the param may like 'tests/my-directory/test_demo.py::TestClassName::test_specific_method'
        # which contains methods to test
        case_express = case_expression.split('::')
        case_path = case_express[0]

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
            self.vm_name = os.path.splitext(case_path.case_name)[0].replace('_', '-')
        else:
            self.vm_name = self.case_expression_in_vm.replace('/', '-').strip('-')


@retry(time_out=WAIT_FOR_VM_SSD_TIMEOUT.value(), check_interval=WAIT_FOR_VM_SSD_CHECK_INTERVAL.value())
def wait_for_vm_sshd(vm_id, vm_ip):
    # type: (str, str) -> None

    Cmd.info('wait for VM[%s, %s] ssh start ...' % (vm_id, vm_ip))

    r, o, e = bash.run('ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s "echo 1"' %
                       (env.SSH_PRIV_KEY_FILE.value(), vm_ip))

    if r != 0:
        raise ZTestError('unable to ssh into root@%s, %s' % (vm_ip, e))


def run_vm(vm_name, image=config.CONFIG.conf.image_tag, kernel=VM_KERNEL.value(), fail_on_existing_vm=True):
    # type: (str, str, str, bool) -> (str, str)

    if not fail_on_existing_vm:
        for vm_id, vm_name, state in ignite.list_all_vm_ids_names_states(include_stopped=True):
            if vm_name == vm_name:
                if state != 'Stopped':
                    ignite.kill_vms([vm_id])

                ignite.rm_vms([vm_id])

    vm_id = ignite.run_vm(image, vm_name, kernel)
    vm_ip = ignite.get_vm_first_ip(vm_id)

    return vm_id, vm_ip


def sync_source(vm_ip, source_root):
    ignored = build_image_cmd.DOCKER_IMAGE_TEST_SOURCE_EXCLUDED.value().split(',')
    ignored = ['--exclude "%s"' % i.strip() for i in ignored]
    if ignored:
        bash.call_with_screen_output(
            'rsync -avz %s -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
            (' '.join(ignored), env.SSH_PRIV_KEY_FILE.value(), source_root, vm_ip,
             env.SOURCE_PARENT_DIR_IN_VM.value()))
    else:
        bash.call_with_screen_output(
            'rsync -avz -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
            (
            env.SSH_PRIV_KEY_FILE.value(), source_root, vm_ip, env.SOURCE_PARENT_DIR_IN_VM.value()))


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
            self.kernel = VM_KERNEL.value()

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

    def _run_test(self):
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

