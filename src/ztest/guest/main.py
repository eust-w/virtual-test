import venv_cmd
import test_cmd
import dryrun_all_cmd
from ztest import cli

commands = [
    venv_cmd.CreateVenv(),
    test_cmd.RunTestCmd(),
    dryrun_all_cmd.DryRunAllCmd()
]


def main():
    cli.run_command(commands)
