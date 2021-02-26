from ztest.core import Cmd
from utils.error import ZTestError
from utils import bash
import case_env
import os.path


def install_zstacklib(venv_activate, path):
    if not os.path.isdir(path):
        raise ZTestError('cannot find zstacklib folder: %s' % path)

    install_sh = os.path.join(path, 'install.sh')
    if not os.path.isfile(install_sh):
        raise ZTestError('cannot find install.sh in %s' % path)

    bash.call_with_screen_output('source %s && bash %s && deactivate' % (venv_activate, install_sh))


class RunTestCmd(Cmd):
    def __init__(self):
        super(RunTestCmd, self).__init__(
            name='test',
            prog='zguest test [options]',
            help='run unit test',
            args=[
                (['--case'], {'help': 'path to the case file', 'dest': 'case', 'required': True}),
                (['--venv'], {'help': 'path to the project venv', 'dest': 'venv', 'required': True}),
                (['--zstacklib'], {'help': 'path to zstacklib source folder, if specified, zstacklib is installed automatically', 'dest': 'zstacklib', 'default': None}),
                (['--dry-run'], {'help': 'dry-run the cases to collect metedata', 'action': 'store_true', 'dest': 'dry_run', 'default': False})
            ]
        )

        self.zstacklib = None
        self.venv_activate = None
        self.dry_run = False

    def _get_case_file_path(self, case_path):
        # the param may like 'tests/my-directory/test_demo.py::TestClassName::test_specific_method'
        # which contains methods to test
        return case_path.split('::')[0]

    def _run(self, args, extra=None):
        if not os.path.isdir(args.venv):
            raise ZTestError('cannot find venv[%s]' % args.venv)

        case_path = self._get_case_file_path(args.case)
        if not os.path.exists(case_path):
            raise ZTestError('cannot find case[%s]' % case_path)

        self.venv_activate = '%s/bin/activate' % args.venv
        self.zstacklib = args.zstacklib
        self.dry_run = args.dry_run

        self._install_zstacklib()
        case_env.CASE_FILE_PATH.set(case_path)
        case_env.DRY_RUN.set(self.dry_run)
        case_env.set_env_variables_for_test_case()
        bash.call_with_screen_output('source %s && pytest -s -v %s && deactivate' % (self.venv_activate, args.case))

    def _install_zstacklib(self):
        if self.zstacklib is None:
            return

        install_zstacklib(self.venv_activate, self.zstacklib)

