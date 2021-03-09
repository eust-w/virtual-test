import os

from utils import json
from ztest import env

CONFIG_FILE = env.env_var('ztest.conf.configFile', str, os.path.join(env.CONF_DIR.value(), 'config.json'))


class Config(object):
    def __init__(self):
        if os.path.isfile(CONFIG_FILE.value()):
            with open(CONFIG_FILE.value(), 'r') as fd:
                content = fd.read()
                self.conf = json.DynamicDict.from_json(content)
        else:
            self.conf = json.DynamicDict.from_dict({})

    def save(self):
        with open(CONFIG_FILE.value(), 'w+') as fd:
            fd.write(self.conf.as_json())

    def set_image_tag(self, tag):
        self.conf.image_tag = tag
        self.save()

    def set_kernel_tag(self, tag):
        self.conf.kernel_tag = tag
        self.save()

    def set_sandbox_tag(self, tag):
        self.conf.sandbox_tag = tag
        self.save()


CONFIG = Config()  # type: Config



