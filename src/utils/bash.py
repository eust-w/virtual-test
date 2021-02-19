import os
import subprocess
import sys

from error import ZTestError


class MissingShellCommand(ZTestError):
    pass


class BashError(ZTestError):
    def __init__(self, msg, cmd, retcode, stdout, stderr):
        self.msg = msg
        self.cmd = cmd
        self.retcode = retcode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return 'shell command failure. %s. details [command: %s, retcode:%s, stdout:%s, stderr: %s]' % \
               (self.msg, self.cmd, self.retcode, self.stdout, self.stderr)


def _merge_shell_stdout_stderr(stdout, stderr):
    # type: (str, str) -> str

    lst = []
    if stdout.strip('\t\n\r ') != '':
        lst.append(stdout)
    if stderr.strip('\t\n\r ') != '':
        lst.append(stderr)

    return ','.join(lst)


def run(command, work_dir=None):
    # type: (str, str) -> (int, str, str)

    p = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         cwd=work_dir,
                         close_fds=True,
                         env=os.environ)
    o, e = p.communicate()
    return p.returncode, str(o), str(e)


def call(command, success_code=0, work_dir=None):
    # type: (str, int, str) -> str

    r, o, e = run(command, work_dir=work_dir)

    if r != success_code:
        raise BashError(msg='command[%s] failed', cmd=command, retcode=r, stdout=o, stderr=e)

    return o


def call_with_screen_output(cmd, raise_error=True, work_dir=None):
    # type: (str, bool, str) -> None

    if work_dir is None:
        print('[BASH]: %s' % cmd)
    else:
        print('[BASH (%s) ]: %s' % (work_dir, cmd))

    p = subprocess.Popen(cmd, shell=True, stdout=sys.stdout,
                         stdin=subprocess.PIPE, stderr=sys.stderr,
                         cwd=work_dir,
                         close_fds=True)
    r = p.wait()
    if r != 0 and raise_error:
        raise BashError(msg='command[%s] failed' % cmd, cmd=cmd, retcode=r, stdout='', stderr='')


def run_with_command_check(command, work_dir=None):
    # type: (str, str) -> (int, str, str)

    r, o, e = run(command, work_dir=work_dir)
    if r == 127:
        raise MissingShellCommand('command[%s] not found in target system, %s' % (command, _merge_shell_stdout_stderr(o, e)))

    return r, o, e


def run_with_err_msg(command, err_msg, work_dir=None):
    # type: (str, str, str) -> str

    r, o, e = run_with_command_check(command, work_dir=work_dir)

    if r != 0:
        raise BashError(msg=err_msg, cmd=command, retcode=r, stdout=o, stderr=e)

    return o

