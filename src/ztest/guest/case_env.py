from ztest import env
import os

TEST_ROOT = env.env_var('ztest.case.testRoot', str, '/root/test_root')
IMAGE_PATH = env.env_var('ztest.case.imagePath', str, os.path.join(TEST_ROOT.value(), 'images/zstack-image-1.4.qcow2'))
VOLUME_DIR = env.env_var('ztest.case.volumeDir', str, os.path.join(TEST_ROOT.value(), 'volumes'))
DEFAULT_ETH_INTERFACE_NAME = env.env_var('ztest.case.defaultEthInterfaceName', str, 'eth0')


env_variables_for_test_case = [
    TEST_ROOT,
    IMAGE_PATH,
    VOLUME_DIR,
    DEFAULT_ETH_INTERFACE_NAME,
]


def set_env_variables_for_test_case():
    for e in env_variables_for_test_case:
        e.set(e.value())

