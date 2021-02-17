from ztest import cli
import run_test_cmd
import test_cmd
import cleanup_cmd
import init_cmd
import build_image_cmd
import update_image_cmd

commands = [
    init_cmd.InitCmd(),
    run_test_cmd.RunTest(),
    test_cmd.TestCmd(),
    cleanup_cmd.CleanupCmd(),
    build_image_cmd.BuildImageCmd(),
    update_image_cmd.UpdateImageCmd()
]


def main():
    cli.run_command(commands)

