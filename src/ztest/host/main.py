from ztest import cli
import test_cmd
import cleanup_cmd
import init_cmd
import build_image_cmd
import update_image_cmd
import coverage_cmd

from utils import bash, misc
import psutil

commands = [
    init_cmd.InitCmd(),
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


def main():
    start_ignited_if_not()
    cli.run_command(commands)

