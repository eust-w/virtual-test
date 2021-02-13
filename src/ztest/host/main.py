from ztest import cli
import run_test
import test_cmd
import cleanup

commands = [
    run_test.RunTest(),
    test_cmd.TestCmd(),
    cleanup.CleanupCmd()
]


def main():
    cli.run_command(commands)

