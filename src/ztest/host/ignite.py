from utils import bash
from utils import json
from utils.error import ZTestError
from ztest import env


def list_all_vm_ids(include_stopped=False):
    # type: (bool) -> list[str]

    if include_stopped:
        o = bash.call('ignite ps -a')
    else:
        o = bash.call('ignite ps')

    vms = o.split('\n')
    if len(vms) == 1:
        vms = []
    else:
        vms = vms[1:]

    vms = [v for v in vms if v.strip(' \t\r')]

    ids = []
    for vm in vms:
        ids.append(vm.split('\t')[0])

    return ids


def list_all_vm_ids_names_states(include_stopped=False):
    # type: (bool) -> list[(str, str, str)]

    if include_stopped:
        o = bash.call('ignite ps -a')
    else:
        o = bash.call('ignite ps')

    vms = [v for v in o.split('\n') if v.strip('\t\r ')]

    if len(vms) == 1:
        vms = []
    else:
        vms = vms[1:]

    vms = [v for v in vms if v.strip(' \t\r')]

    id_names = []
    for vm in vms:
        ss = vm.split('\t')
        id_names.append((ss[0], ss[-1], ss[-4]))

    return id_names


def get_image(image_id):
    # type: (str) -> json.DynamicDict

    o = bash.call('ignite inspect image %s' % image_id)
    return json.loads(o)


def list_all_image_ids():
    # type: () -> list[str]

    o = bash.call('ignite image ls')
    images = [i for i in o.split('\n') if i.strip('\t\r ')]
    if len(images) == 1:
        images = []
    else:
        images = images[1:]

    ids = [i.split('\t')[0] for i in images]
    return ids


def list_all_kernel_ids():
    # type: () -> list[str]

    o = bash.call('ignite kernel ls')
    images = [i for i in o.split('\n') if i.strip('\t\r ')]
    if len(images) == 1:
        images = []
    else:
        images = images[1:]

    ids = [i.split('\t')[0] for i in images]
    return ids


def find_image(tag):
    # type: (str) -> json.DynamicDict
    for i in list_all_images():
        if i.spec.oci == tag:
            return i

    return None


def rm_image(image_id):
    # type: (str) -> None

    bash.call_with_screen_output('ignite image rm %s' % image_id)


def get_kernel(kernel_id):
    # type: (str) -> json.DynamicDict
    o = bash.call('ignite inspect kernel %s' % kernel_id)
    return json.loads(o)


def find_kernel(tag):
    # type: (str) -> json.DynamicDict

    for k in list_all_kernels():
        if tag == k.spec.oci:
            return k

    return None


def list_all_kernels():
    # type: () -> list[json.DynamicDict]

    kernels = []
    for k in list_all_kernel_ids():
        kernels.append(get_kernel(k))

    return kernels


def list_all_images():
    # type: () -> list[json.DynamicDict]

    images = []
    for i in list_all_image_ids():
        images.append(get_image(i))

    return images


def get_vm(vm_id):
    # type: (str) -> json.DynamicDict

    o = bash.call('ignite inspect vm %s' % vm_id)
    return json.loads(o)


def list_all_vms(include_stopped=False):
    # type: (bool) -> list[dict]

    ids = list_all_vm_ids(include_stopped)
    vms = []
    for id in ids:
        vms.append(get_vm(id))

    return vms


def get_vm_ips(vm_id):
    # type: (str) -> list[str]

    vm = get_vm(vm_id)
    return vm.status.network.ipAddresses


def get_vm_first_ip(vm_id):
    # type: (str) -> str
    return get_vm_ips(vm_id)[0]


def run_vm(image, vm_name, kernel=None, memory=None, cpu=None, disk=None):
    # type: (str, str, str, str, int, str) -> str

    cmd = ['ignite run %s --name %s --ssh=%s' % (image, vm_name, env.SSH_PUB_KEY_FILE.value())]
    if kernel is not None:
        cmd.append('-k %s' % kernel)
    if memory is not None:
        cmd.append('--memory %s' % memory)
    if cpu is not None:
        cmd.append('--cpus %s' % cpu)
    if disk is not None:
        cmd.append('--size %s' % disk)

    bash.call_with_screen_output(' '.join(cmd))

    for id, name, _ in list_all_vm_ids_names_states():
        if vm_name == name:
            return id

    raise ZTestError('unable to find vm[name:%s], run "ignite ps" to check' % vm_name)


def kill_vms(ids):
    # type: (list[str]) -> None

    if ids:
        bash.call_with_screen_output('ignite kill %s' % ' '.join(ids))


def rm_vms(ids):
    # type: (list[str]) -> None

    if ids:
        bash.call_with_screen_output('ignite rm %s' % ' '.join(ids))


def import_image(tag):
    # type: (str) -> None
    bash.call_with_screen_output('ignite --runtime docker image import %s' % tag)


def bash_call_with_screen_output(vm_id, cmd, priv_key_path=env.SSH_PRIV_KEY_FILE.value(), log_file=None):
    # type: (str, str, str, str) -> None

    if log_file is None:
        cmd = "ignite exec %s '%s' -i %s" % (vm_id, cmd, priv_key_path)
    else:
        cmd = "set -o pipefail; ignite exec %s '%s' -i %s | tee %s" % (vm_id, cmd, priv_key_path, log_file)
    bash.call_with_screen_output(cmd)


def cp(src, dst, pri_key=env.SSH_PRIV_KEY_FILE.value()):
    bash.call_with_screen_output('ignite cp %s %s -i %s' % (src, dst, pri_key))


def cleanup_vm_by_name(vm_name):
    # type: (str) -> None

    for vm_id, name, state in list_all_vm_ids_names_states(include_stopped=True):
        if name == vm_name:
            if state != 'Stopped':
                kill_vms([vm_id])

            rm_vms([vm_id])

