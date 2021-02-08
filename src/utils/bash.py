import subprocess
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


def run(command):
    # type: (str) -> (int, str, str)

    p = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         close_fds=True)
    o, e = p.communicate()
    return p.returncode, str(o), str(e)


def call(command, success_code=0):
    # type: (str, int) -> str

    r, o, e = run(command)

    if r != success_code:
        raise BashError(msg='command[%s] failed', cmd=command, retcode=r, stdout=o, stderr=e)

    return o


def run_with_command_check(command):
    # type: (str) -> (int, str, str)

    r, o, e = run(command)
    if r == 127:
        raise MissingShellCommand('command[%s] not found in target system, %s' % (cmd, _merge_shell_stdout_stderr(o, e)))

    return r, o, e


def run_with_err_msg(command, err_msg):
    # type: (str, str) -> str

    r, o, e = run_with_command_check(command)

    if r != 0:
        raise BashError(msg=err_msg, cmd=command, retcode=r, stdout=o, stderr=e)

    return o

