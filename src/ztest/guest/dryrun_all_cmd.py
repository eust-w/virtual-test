import os

import case_env
import test_cmd
from utils import bash
from ztest import env
from ztest.core import Cmd


class DryRunAllCmd(Cmd):
    def __init__(self):
        super(DryRunAllCmd, self).__init__(
            name='dry-run-all',
            help='dry-run all test cases'
        )

    def _run(self, args, extra=None):
        venv_dirs = []

        for d in os.listdir(env.TEST_ENV_DIR_IN_VM.value()):
            p = os.path.join(env.TEST_ENV_DIR_IN_VM.value(), d)
            if os.path.isdir(p):
                venv_dirs.append((d, p))

        to_run = []
        for project_name, venv_path in venv_dirs:
            to_run.append((os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), project_name), venv_path))

        zstacklib_dir = os.path.join(env.ZSTACK_UTILITY_SRC_IN_VM.value(), 'zstacklib')
        for src_dir, venv_path in to_run:
            venv_activate = os.path.join(venv_path, 'bin/activate')
            test_cmd.install_zstacklib(venv_activate, zstacklib_dir)

            case_env.CASE_FILE_PATH.set(src_dir)
            case_env.DRY_RUN.set(True)
            case_env.set_env_variables_for_test_case()

            bash.call_with_screen_output(
                'source %s && pytest -s -v %s && deactivate' % (venv_activate, src_dir),
                ret_code=[0, 5]  # return code 5 means no test case
            )


