import venv_cmd
import test_cmd
import dryrun_all_cmd
from ztest import cli
from ztest import env
import os
from utils import json

commands = [
    venv_cmd.CreateVenv(),
    test_cmd.RunTestCmd(),
    dryrun_all_cmd.DryRunAllCmd()
]


def load_env_vars():
    if not os.path.isfile(env.env_file_path_in_vm):
        return

    with open(env.env_file_path_in_vm, 'r') as fd:
        d = json.loads_as_dict(fd.read())
        for k, v in d.iteritems():
            os.environ[k] = v


def main():
    load_env_vars()
    cli.run_command(commands)
