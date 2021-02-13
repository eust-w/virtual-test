from ztest.core import Cmd
import ignite


class CleanupCmd(Cmd):
    def __init__(self):
        super(CleanupCmd, self).__init__(
            name='cleanup',
            help='cleanup test environment, including removing all vms'
        )

    def _cleanup_vms(self):
        running_vm_ids = ignite.list_all_vm_ids()
        ignite.kill_vms(running_vm_ids)
        all_vm_ids = ignite.list_all_vm_ids(include_stopped=True)
        ignite.rm_vms(all_vm_ids)

    def _run(self, args, extra=None):
        self._cleanup_vms()

