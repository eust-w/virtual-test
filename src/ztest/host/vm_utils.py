import os

from utils import retry, bash, ZTestError, defer
from ztest import config, env
from ztest.core import Cmd
from ztest.host import ignite, build_image_cmd
import tempfile
import json


def run_vm(vm_name, image=config.CONFIG.conf.image_tag, kernel=config.CONFIG.conf.kernel_tag, fail_on_existing_vm=True):
    # type: (str, str, str, bool) -> (str, str)

    if not fail_on_existing_vm:
        ignite.cleanup_vm_by_name(vm_name)

    vm_id = ignite.run_vm(image, vm_name, kernel)
    vm_ip = ignite.get_vm_first_ip(vm_id)

    return vm_id, vm_ip


WAIT_FOR_VM_SSD_TIMEOUT = env.env_var('ztest.vm.waitSshdTimeout', int, 30)
WAIT_FOR_VM_SSD_CHECK_INTERVAL = env.env_var('ztest.vm.checkSshdUpInterval', float, 0.5)


@retry(time_out=WAIT_FOR_VM_SSD_TIMEOUT.value(), check_interval=WAIT_FOR_VM_SSD_CHECK_INTERVAL.value())
def wait_for_vm_sshd(vm_id, vm_ip):
    # type: (str, str) -> None

    Cmd.info('wait for VM[%s, %s] ssh start ...' % (vm_id, vm_ip))

    r, o, e = bash.run('ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@%s "echo 1"' %
                       (env.SSH_PRIV_KEY_FILE.value(), vm_ip))

    if r != 0:
        raise ZTestError('unable to ssh into root@%s, %s' % (vm_ip, e))


def sync_source(vm_ip, source_root):
    ignored = build_image_cmd.DOCKER_IMAGE_TEST_SOURCE_EXCLUDED.value().split(',')
    ignored = ['--exclude "%s"' % i.strip() for i in ignored]
    if ignored:
        bash.call_with_screen_output(
            'rsync -avz %s -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
            (' '.join(ignored), env.SSH_PRIV_KEY_FILE.value(), source_root, vm_ip,
             env.SOURCE_PARENT_DIR_IN_VM.value()))
    else:
        bash.call_with_screen_output(
            'rsync -avz -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
            (
                env.SSH_PRIV_KEY_FILE.value(), source_root, vm_ip, env.SOURCE_PARENT_DIR_IN_VM.value()))


@defer.protect
def create_env_var_file_in_vm(vm_id):
    # type: (str) -> None

    env_vars = env.get_vm_env_vars()
    if not env_vars:
        return

    fd, filename = tempfile.mkstemp()
    os.write(fd, json.dumps(env_vars))
    os.close(fd)
    defer.defer(lambda: os.remove(filename))

    ignite.cp(filename, '%s:%s' % (vm_id, env.env_file_path_in_vm))




