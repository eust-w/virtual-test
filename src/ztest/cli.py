import argparse
import sys

from utils.error import ZTestError


def _split_cmd_and_checkers(cmd):
    if isinstance(cmd, tuple):
        return cmd[0], cmd[1:]
    else:
        return cmd, []


def run_command(commands):
    # type: (list) -> None

    parser = argparse.ArgumentParser(description="""\
    ZTest tool
    """)
    sub_parser = parser.add_subparsers(help='sub-command help', dest="sub_command_name")

    for cmd in commands:
        cmd, _ = _split_cmd_and_checkers(cmd)
        sp = sub_parser.add_parser(name=cmd.name, help=cmd.help, prog='ztest-guest cmd_name', description=cmd.description)
        if cmd.args:
            for args in cmd.args:
                ag, kwargs = args
                sp.add_argument(*ag, **kwargs)

    opts, extra = parser.parse_known_args()

    cmd = None
    for c in commands:
        cc, _ = _split_cmd_and_checkers(c)
        if cc.name == opts.sub_command_name:
            cmd = c
            break

    if cmd is None:
        raise Exception('unknown command: %s' % opts.sub_command_name)

    cmd, checkers = _split_cmd_and_checkers(cmd)
    for checker in checkers:
        checker()

    cmd.run(opts, extra)
