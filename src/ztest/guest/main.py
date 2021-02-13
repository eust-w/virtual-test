import create_env
import install
import run_test
from ztest import cli

commands = [
    create_env.CreateVenv(),
    install.InstallCmd(),
    run_test.RunTestCmd()
]


def main():
    cli.run_command(commands)
