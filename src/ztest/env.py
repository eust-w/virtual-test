from utils.error import ZTestError
import typing
import os
import threading


_local = threading.local()
_local.vm_env = {}


class EnvVariable(object):
    def __init__(self, name, type, default=None):
        self.name = name
        self.type = type
        self.default = default

    def set(self, value):
        os.environ[self.name] = str(value)

    def value(self):
        v = os.getenv(self.name, None)
        try:
            if v is not None:
                return self.type(v)
            else:
                return self.type(self.default)
        except TypeError as ex:
            raise ZTestError('environment[%s] is defined as type[%s] but get %s. %s' %
                            (self.name, self.type, type(v), str(ex)))


def env_var(name, the_type, default=None):
    # type: (str, typing.Type, typing.Any) -> EnvVariable

    return EnvVariable(name=name, type=the_type, default=default)


def set_env_var(name, value):
    # type: (str, typing.Any) -> None

    os.environ[name] = str(value)


CONF_DIR = env_var('ztest.conf.dir', str, os.path.expanduser('~/.ztest'))
SOURCE_PARENT_DIR_IN_VM = env_var('ztest.vm.source.parent.dir', str, '/root')
SSH_PRIV_KEY_FILE = env_var('ztest.ssh.privatekey', str, os.path.join(CONF_DIR.value(), 'ssh/id_rsa'))
SSH_PUB_KEY_FILE = env_var('ztest.ssh.privatekey', str, os.path.join(CONF_DIR.value(), 'ssh/id_rsa.pub'))
TEST_ENV_DIR_IN_VM = env_var('ztest.vm.testVenvDir', str, '/root/test-venv')
ZSTACK_UTILITY_SRC_IN_VM = env_var('ztest.vm.zstackUtilityDir', str, '/root/zstack-utility')
TEST_FOR_OUTPUT_DIR = env_var('ztest.case.testForDir', str, default='/root/ztest-test-for')

if not os.path.isdir(CONF_DIR.value()):
    os.makedirs(CONF_DIR.value())


def set_vm_env_var(key, value):
    # type: (str, object) -> None

    _local.vm_env[key] = str(value)


def set_vm_env_vars(env_vars):
    # type: (dict) -> None

    _local.vm_env.update(env_vars)


def get_vm_env_vars():
    return _local.vm_env


env_file_path_in_vm = '/root/env_vars.json'


def set_ssh_private_key_to_vm_env_vars():
    with open(SSH_PRIV_KEY_FILE.value(), 'r') as fd:
        set_vm_env_var('ztest.vm.ssh.privKeyText', fd.read())
