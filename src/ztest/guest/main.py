import argparse
import sys

import create_env
import install
import run_test
from utils.error import ZTestError

commands = [
    create_env.CreateVenv(),
    install.InstallCmd(),
    run_test.RunTestCmd()
]


def main():
    parser = argparse.ArgumentParser(description="""\
    ZTest guest tool
    """)
    sub_parser = parser.add_subparsers(help='sub-command help', dest="sub_command_name")

    for cmd in commands:
        sp = sub_parser.add_parser(name=cmd.name, help=cmd.help, prog='ztest-guest cmd_name', description=cmd.description)
        if cmd.args:
            for args in cmd.args:
                ag, kwargs = args
                sp.add_argument(*ag, **kwargs)

    opts, extra = parser.parse_known_args()

    cmd = None
    for c in commands:
        if c.name == opts.sub_command_name:
            cmd = c
            break

    if cmd is None:
        raise Exception('unknown command: %s' % opts.sub_command_name)

    try:
        cmd.run(opts, extra)
    except ZTestError as e:
        print(str(e))
        sys.exit(1)
