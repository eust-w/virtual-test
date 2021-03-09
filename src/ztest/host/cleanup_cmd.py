from ztest.core import Cmd
from utils import bash
import ignite
import docker
from ztest import env
from utils.error import ZTestError

FIRECRAKER_VM_DIR = env.env_var('ZTEST_FIRECRACKER_VM_DIR', str, '/var/lib/firecracker/vm/')


class CleanupCmd(Cmd):
    def __init__(self):
        super(CleanupCmd, self).__init__(
            name='cleanup',
            help='cleanup test environment, including removing all vms'
        )

    def _cleanup_docker(self):
        containers = docker.list_containers()
        container_ids = [c.ID for c in containers]
        docker.kill_containers(container_ids)
        container_ids = [c.ID for c in docker.list_containers(included_stopped=True)]
        docker.rm_containers(container_ids)


    def _cleanup_ignite(self):
        running_vm_ids = ignite.list_all_vm_ids()
        ignite.kill_vms(running_vm_ids)
        all_vm_ids = ignite.list_all_vm_ids(include_stopped=True)
        ignite.rm_vms(all_vm_ids)

    def _cleanup_containerd(self):
        containers = bash.call('ctr -n firecracker containers ls').split('\n')
        containers = [c for c in containers if c.strip(' \t\r')]
        if len(containers) == 1:
            # empty
            return

        containers = containers[1:]
        container_ids = [c.split()[0] for c in containers]

        bash.call('ctr -n firecracker containers del %s' % ' '.join(container_ids))

    def _cleanup_firecracker_vm_dir(self):
        bash.call('rm -rf %s/*' % FIRECRAKER_VM_DIR.value())

    def _cleanup_vms(self):
        ignite_err = None
        try:
            self._cleanup_ignite()
        except Exception as e:
            ignite_err = e

        self._cleanup_containerd()
        self._cleanup_firecracker_vm_dir()

        vms = ignite.list_all_vm_ids(include_stopped=True)
        if vms:
            vm_ids = ' '.join(vms)
            if not ignite_err:
                raise ZTestError('failed to cleanup, there are still vms[%s] remained in ignited' % vm_ids)
            else:
                raise ZTestError('failed to cleanup, there are still vms[%s] remained in ignited, %s' % (vm_ids, ignite_err))

        else:
            if ignite_err:
                self.info('\nPlease ignore any error log, the environment was forced cleanup')

    def _run(self, args, extra=None):
        self._cleanup_vms()
        self._cleanup_docker()

