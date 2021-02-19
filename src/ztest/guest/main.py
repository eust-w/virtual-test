import venv_cmd
import test_cmd
from ztest import cli

commands = [
    venv_cmd.CreateVenv(),
    test_cmd.RunTestCmd()
]


def main():
    cli.run_command(commands)
