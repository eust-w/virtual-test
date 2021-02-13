import ztest.core
import ignite


class TestCmd(ztest.core.Cmd):
    def __init__(self):
        super(TestCmd, self).__init__(name='test', help='test')

    def _run(self, args, extra=None):
        ignite.list_all_vm_ids_and_names()
