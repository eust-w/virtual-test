from utils.error import ZTestError
import typing
import os


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
SSH_PRIV_KEY_FILE = env_var('ztest.ssh.privatekey', str, os.path.join(CONF_DIR.value(), '/ssh/id_rsa'))

if not os.path.isdir(CONF_DIR.value()):
    os.makedirs(CONF_DIR.value())

