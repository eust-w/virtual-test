from utils import bash
from ztest import env
from ztest.host import ignite


def sync_source_to_vm(vm_id, src_dir):
    # type: (str, str) -> None

    ip = ignite.get_vm_first_ip(vm_id)
    bash.call_with_screen_output('rsync -avz -e "ssh -i %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --delete --progress %s root@%s:%s' %
                                 (env.SSH_PRIV_KEY_FILE.value(), src_dir, ip, env.SOURCE_PARENT_DIR_IN_VM.value()))

