import ast_utils
from utils import json, logging
from utils.error import ZTestError
from ztest import config, env
import vm_utils
import ignite
import traceback


logger = logging.get_logger(__name__)


class VmSetup(object):
    def __init__(self, vm_info):
        # type: (json.DynamicDict) -> VmSetup

        self.vm_info = vm_info

    def setup(self):
        vm_name = self.vm_info.name
        image = self.vm_info.image if self.vm_info.image is not None else config.CONFIG.conf.image_tag
        kernel = self.vm_info.kernel if self.vm_info.kernel is not None else config.CONFIG.conf.kernel_tag
        cpu = self.vm_info.cpu
        memory = self.vm_info.memory
        disk = self.vm_info.disk

        ignite.cleanup_vm_by_name(vm_name)
        vm_id = ignite.run_vm(vm_name=vm_name, image=image, kernel=kernel, cpu=cpu, memory=memory, disk=disk)
        vm_ip = ignite.get_vm_first_ip(vm_id)
        vm_utils.wait_for_vm_sshd(vm_id, vm_ip)

        vm_info = {
            'ip': vm_ip
        }

        env.set_vm_env_var('ztest.vm.%s' % vm_name, json.dumps(vm_info))

        def cleanup():
            ignite.kill_vms([vm_id])
            ignite.rm_vms([vm_id])

        return cleanup


def run_setup(case_path):
    # type: (str) -> function

    cleanup_funcs = []

    def cleanup():
        for clean in cleanup_funcs:
            try:
                clean()
            except Exception:
                logger.warn('runc cleanup function failed, %s' % traceback.format_exc())

    env_setup = ast_utils.parse_env_setup(case_path)
    if env_setup is None:
        return cleanup

    env_setup = json.DynamicDict.from_dict(env_setup)
    if env_setup.vm is not None:
        if not isinstance(env_setup.vm, list):
            raise ZTestError('"vm" field in __ENV_SETUP__ must be a list, but get a %s\n __ENV_SETUP__ dump: %s\n' % (type(env_setup.vm), json.dumps(env_setup)))

        for vm in env_setup.vm:
            cleanup_funcs.append(VmSetup(vm).setup())

    return cleanup

