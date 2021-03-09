import os
import sys

from ztest import cli, env
from utils.error import ZTestError
import test_cmd
import cleanup_cmd
import build_image_cmd
import update_image_cmd
import coverage_cmd
import import_image_cmd
import ssh_keys
import export_image_cmd
import init_cmd
import set_default_cmd
from init_cmd import init_check

from utils import bash, misc
import psutil
import traceback

commands = [
    (test_cmd.RunTest(), init_check),
    cleanup_cmd.CleanupCmd(),
    build_image_cmd.BuildImageCmd(),
    (update_image_cmd.UpdateImageCmd(), init_check),
    (coverage_cmd.CoverageCmd(), init_check),
    import_image_cmd.ImportImageCmd(),
    export_image_cmd.ExportImageCmd(),
    init_cmd.InitCmd(),
    set_default_cmd.SetDefaultCmd()
]


def err_exit(err):
    sys.stderr.write('ERROR: %s\n' % err)
    sys.exit(1)


def check_installation():
    _, o, _ = bash.run('whoami')
    if o.strip('\n\t\r ') != 'root':
        err_exit('please run as root user')

    r, _, _ = bash.run('which ignite')
    if r != 0:
        err_exit('ignite not found, run "install-ztest" first')

    r, _, _ = bash.run('which ignited')
    if r != 0:
        err_exit('ignited not found, run "install-ztest" first')

    r, _, _ = bash.run('which docker')
    if r != 0:
        err_exit('docker not found, run "install-ztest" first')


def start_ignited_if_not():
    is_running = False

    for p in psutil.process_iter():
        cmdline = p.cmdline()
        if 'ignited' in cmdline:
            is_running = True
            break

    if not is_running:
        bash.call_with_screen_output('nohup ignited daemon --log-level debug &')

        @misc.retry(5, 0.5)
        def wait_for_start():
            bash.call('ignite ps')

        wait_for_start()


def create_ssh_key_if_not_exists():
    if not os.path.isfile(env.SSH_PRIV_KEY_FILE.value()):
        d = os.path.dirname(env.SSH_PRIV_KEY_FILE.value())
        if not os.path.isdir(d):
            os.makedirs(d)

        with open(env.SSH_PRIV_KEY_FILE.value(), 'w+') as fd:
            fd.write(ssh_keys.private_key)

        os.chmod(env.SSH_PRIV_KEY_FILE.value(), 0600)

    if not os.path.isfile(env.SSH_PUB_KEY_FILE.value()):
        d = os.path.dirname(env.SSH_PUB_KEY_FILE.value())
        if not os.path.isdir(d):
            os.makedirs(d)

        with open(env.SSH_PUB_KEY_FILE.value(), 'w+') as fd:
            fd.write(ssh_keys.pub_key)


def main():
    check_installation()
    create_ssh_key_if_not_exists()
    start_ignited_if_not()
    try:
        cli.run_command(commands)
    except ZTestError as e:
        if env.DEBUG.value() != 'None':
            c = traceback.format_exc()
            sys.stderr.write(c)

        err_exit(e.message)

