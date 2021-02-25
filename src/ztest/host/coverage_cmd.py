import os

from ztest.core import Cmd
from utils.error import ZTestError
from utils import json
import ast_utils


class CoverageCmd(Cmd):
    def __init__(self):
        super(CoverageCmd, self).__init__(
            name='coverage',
            help='coverage report',
            args=[
                (['--handler', '-hl'], {'help': 'report agent handler coverage', 'action': 'store_true', 'dest': 'handler', 'default': False}),
                (['--src', '-s'], {'help': 'path to source file/folder', 'dest': 'src', 'required': True})
            ]
        )

        self.handler = False
        self.src = None

    def _run(self, args, extra=None):
        self.src = args.src
        self.handler = args.handler

        if not os.path.exists(self.src):
            raise ZTestError('%s not found' % self.src)

        if not any([self.handler]):
            raise ZTestError('please specify at least one action option (--handler)')

        if self.handler:
            self._report_handler()

    def _report_handler(self):
        if os.path.isfile(self.src):
            src_files = [self.src]
        else:
            src_files = []
            for root, _, files in os.walk(self.src):
                for f in files:
                    if not f.endswith('.py'):
                        continue

                    file_path = os.path.join(root, f)
                    src_files.append(file_path)

        results = {}
        for src in src_files:
            results.update(ast_utils.collect_agent_handler_in_file(src))

        print json.dumps(results)




