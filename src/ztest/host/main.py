import os

from ztest import cli, env
import test_cmd
import cleanup_cmd
import build_image_cmd
import update_image_cmd
import coverage_cmd
import ssh_keys

from utils import bash, misc
import psutil

commands = [
    test_cmd.RunTest(),
    cleanup_cmd.CleanupCmd(),
    build_image_cmd.BuildImageCmd(),
    update_image_cmd.UpdateImageCmd(),
    coverage_cmd.CoverageCmd()
]


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
    create_ssh_key_if_not_exists()
    start_ignited_if_not()
    cli.run_command(commands)

