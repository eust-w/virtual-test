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
                return self.default
        except TypeError as ex:
            raise ZTestError('environment[%s] is defined as type[%s] but get %s. %s' %
                            (self.name, self.type, type(v), str(ex)))


def env_var(name, type=str, default=None):
    # type: (str, typing.Type, typing.Any) -> EnvVariable

    return EnvVariable(name=name, type=type, default=default)


def set_env_var(name, value):
    # type: (str, typing.Any) -> None

    os.environ[name] = str(value)