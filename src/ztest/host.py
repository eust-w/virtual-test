from core import Cmd, CmdOptionError
from env import env_var


SOURCE_DIR = env_var('ztest.source.dir', str, None)


class RunTest(Cmd):
    def __init__(self):
        super(RunTest, self).__init__(
            name='run-test',
            help='run a test case',
            prog='ztest run-test [options] case_file | full_path_to_case_file',
            description='Example: ztest run-test test_start_vm.py',
            args=[
                (['--src'], {'help': 'path to root folder of source code', 'dest': 'src', 'default': None})
            ]
        )

        self.case_path = None

    def _get_full_case_path(self, src_dir, case_file):
        pass

    def _run(self, args, extra=None):
        if not extra:
            raise CmdOptionError('case file not specified')

        case_file = extra[0]

        if not args.src:
            args.src = SOURCE_DIR.value()

        if not args.src:
            raise CmdOptionError('the root folder of source code not specified. you can provide it by specifying --src or set'
                                 ' environment variable[%s]' % SOURCE_DIR.name)

        self.case_path = self._get_full_case_path(args.src, case_file)
