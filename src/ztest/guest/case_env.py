from ztest import env


IMAGE_PATH = env.env_var('ztest.case.imagePath', str, '/root/test_root/images/zstack-image-1.4.qcow2')
DEFAULT_ETH_INTERFACE_NAME = env.env_var('ztest.case.defaultEthInterfaceName', str, 'eth0')


env_variables_for_test_case = [
    IMAGE_PATH,
]


def set_env_variables_for_test_case():
    for e in env_variables_for_test_case:
        e.set(e.value())

