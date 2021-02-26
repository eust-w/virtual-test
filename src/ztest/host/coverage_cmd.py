import os

from ztest.core import Cmd
from utils.error import ZTestError
from utils import json
import ast_utils
import test_cmd
import ignite
from ztest import env
import tempfile


class HandlerCoverBy(object):
    def __init__(self, file_name, function_name):
        self.file_name = file_name
        self.function_name = function_name


class HandlerStat(object):
    def __init__(self, handler_name, in_file, line_num):  # type: (str, str, int, list) -> HandlerStat
        self.handler_name = handler_name
        self.cover_by = []
        self.in_file = in_file
        self.line_num = line_num

    def __str__(self):
        return '%s (%s:%s) covered %s times' % (self.handler_name, self.in_file, self.line_num, len(self.cover_by))

    def is_covered(self):
        return len(self.cover_by) > 0


class CoverageCmd(Cmd):
    def __init__(self):
        super(CoverageCmd, self).__init__(
            name='coverage',
            help='coverage report',
            args=[
                (['--handler', '-hl'], {'help': 'report agent handler coverage, the JSON result is written to ./ztest_handler_coverage.json', 'action': 'store_true', 'dest': 'handler', 'default': False}),
                (['--src', '-s'], {'help': 'path to source file/folder', 'dest': 'src', 'required': True}),
                (['-j', '--json'], {'help': 'output in json format', 'dest': 'json', 'action': 'store_true', 'required': False, 'default': False})
            ]
        )

        self.handler = False
        self.src = None
        self.json = False

    def _run(self, args, extra=None):
        self.src = args.src
        self.handler = args.handler
        self.json = args.json

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

        results = {}  # type: dict[str, ast_utils.HandlerInfo]
        for src in src_files:
            results.update(ast_utils.collect_agent_handler_in_file(src))

        vm_id, vm_ip = test_cmd.run_vm('dry-run', fail_on_existing_vm=False)
        test_cmd.wait_for_vm_sshd(vm_id, vm_ip)

        case_path = test_cmd.CasePath(self.src)
        test_cmd.sync_source(vm_ip, case_path.source_root)

        tmp_dir = tempfile.mkdtemp()
        ignite.bash_call_with_screen_output(vm_id, 'zguest dry-run-all')
        ignite.cp('%s:%s' % (vm_id, env.TEST_FOR_OUTPUT_DIR.value()), tmp_dir)

        test_for_dir = os.path.join(tmp_dir, os.path.basename(env.TEST_FOR_OUTPUT_DIR.value()))

        tested_handlers = {}

        for f in os.listdir(test_for_dir):
            file_path = os.path.join(test_for_dir, f)
            with open(file_path, 'r') as fd:
                test_for = json.loads(fd.read())

            for tr in test_for.test_for:
                for h in tr.handlers:
                    lst = tested_handlers.get(h)
                    if lst is None:
                        lst = []

                    lst.append((test_for.case_path, tr))
                    tested_handlers[h] = lst

        handler_stats = []

        for handler_name, info in results.iteritems():
            hs = HandlerStat(
                handler_name=handler_name,
                in_file=info.file_path,
                line_num=info.line_num
            )

            handler_stats.append(hs)

            lst = tested_handlers.get(handler_name)
            if lst is None:
                continue

            for case_path, tr in lst:
                hs.cover_by.append(HandlerCoverBy(file_name=case_path, function_name=tr.func))

        jstr = json.dumps(handler_stats)
        with open('ztest_handler_coverage.json', 'w+') as fd:
            fd.write(jstr)

        covered_handlers = []
        uncovered_handlers = []

        for hs in handler_stats:
            if not hs.is_covered():
                uncovered_handlers.append(hs)
            else:
                covered_handlers.append(hs)

        info = [
            "\n\n\nCOVERED handlers\n",
            '\n'.join(str(h) for h in covered_handlers),
            "\n\n\nUNCOVERED handlers:\n",
            '\n'.join(str(h) for h in uncovered_handlers),
        ]

        print('\n'.join(info))




