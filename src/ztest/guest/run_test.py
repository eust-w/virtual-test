from ztest.core import Cmd
from utils.error import ZTestError
from utils import bash
import os.path


class RunTestCmd(Cmd):
    def __init__(self):
        super(RunTestCmd, self).__init__(
            name='test',
            prog='zguest test [options]',
            help='run unit test',
            args=[
                (['--case'], {'help': 'path to the case file', 'dest': 'case', 'required': True}),
                (['--venv'], {'help': 'path to the project venv', 'dest': 'venv', 'required': True})
            ]
        )

    def _run(self, args, extra=None):
        if not os.path.isdir(args.venv):
            raise ZTestError('cannot find venv[%s]' % args.venv)

        if not os.path.isfile(args.case):
            raise ZTestError('cannot find case[%s]' % args.case)

        venv_activate = '%s/bin/activate' % args.venv
        bash.call_with_screen_output('source %s && pytest %s -s && deactivate' % (venv_activate, args.case))
