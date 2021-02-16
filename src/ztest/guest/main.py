import create_venv
import install
import run_test
from ztest import cli

commands = [
    create_venv.CreateVenv(),
    install.InstallCmd(),
    run_test.RunTestCmd()
]


def main():
    cli.run_command(commands)
