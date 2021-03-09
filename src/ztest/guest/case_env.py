from ztest import env
import os
from utils import logging


logger = logging.get_logger(__name__)

TEST_ROOT = env.env_var('ZTEST_CASE_TEST_ROOT', str, '/root/test_root')
IMAGE_PATH = env.env_var('ZTEST_CASE_IMAGE_PATH', str, os.path.join(TEST_ROOT.value(), 'images/zstack-image-1.4.qcow2'))
VOLUME_DIR = env.env_var('ZTEST_CASE_VOLUME_DIR', str, os.path.join(TEST_ROOT.value(), 'volumes'))
SNAPSHOT_DIR = env.env_var('ZTEST_CASE_SNAPSHOT_DIR', str, os.path.join(TEST_ROOT.value(), 'snapshots'))
DEFAULT_ETH_INTERFACE_NAME = env.env_var('ZTEST_CASE_DEFAULT_ETH_INTERFACE_NAME', str, 'eth0')
CASE_FILE_PATH = env.env_var('ZTEST_CASE_FILE_PATH', str, None)
DRY_RUN = env.env_var('ZTEST_CASE_DRY_RUN', bool, False)


env_variables_for_test_case = [
    TEST_ROOT,
    IMAGE_PATH,
    VOLUME_DIR,
    SNAPSHOT_DIR,
    DEFAULT_ETH_INTERFACE_NAME,
    env.ZSTACK_UTILITY_SRC_IN_VM,
    CASE_FILE_PATH,
    DRY_RUN,
    env.TEST_FOR_OUTPUT_DIR,
]


def set_env_variables_for_test_case():
    for e in env_variables_for_test_case:
        e.set(e.value())
        logger.debug('set case environment variable: %s=%s' % (e.name, e.value()))

