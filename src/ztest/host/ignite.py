from utils import bash
from utils import json
from utils.error import ZTestError


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


def list_all_vm_ids_and_names(include_stopped=False):
    # type: (bool) -> list[(str, str)]

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

    id_names = []
    for vm in vms:
        ss = vm.split('\t')
        id_names.append((ss[0], ss[-1]))

    return id_names


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


def run_vm(image, vm_name):
    # type: (str) -> str

    bash.call('ignite run %s --name %s' % (image, vm_name))

    for id, name in list_all_vm_ids_and_names():
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

