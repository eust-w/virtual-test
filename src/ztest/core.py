from utils.error import ZTestError
from utils import bash
import sys


class CmdOptionError(ZTestError):
    pass


class Cmd(object):
    def __init__(self, name, help, prog=None, description='', args=None):
        # type: (str, str, str, str, list) -> Cmd

        self.name = name
        self.help = help
        self.description = description
        self.args = args
        self.prog = prog

    def _check(self):
        pass

    def _run(self, args, extra=None):
        raise Exception('not implemented')

    def run(self, args, extra=None):
        self._check()
        self._run(args, extra)

    @staticmethod
    def info(msg):
        sys.stdout.write('%s\n' % msg)

    @staticmethod
    def err(err):
        sys.stderr.write('ERROR: %s\n' % err)


def check_tool(name):
    r, o, e = bash.run('which %s' % name)
    if r != 0:
        raise ZTestError('command[%s] not found in the system' % name)


def check_tools(names):
    for name in names:
        check_tool(name)
