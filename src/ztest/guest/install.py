from utils import bash
from ztest.core import Cmd
from utils.error import ZTestError
import os.path


class InstallCmd(Cmd):
    def __init__(self):
        super(InstallCmd, self).__init__(
            name='install',
            help='install zstack-utility package',
            prog='zguest install [options]',
            args=[
                (['--pkg'], {'help': 'the package file, e.g. kvmagent-4.0.0.tar.gz', 'dest': 'pkg', 'required': True}),
                (['--deps'], {'help': 'dependent library files for the package', 'dest': 'deps', 'default': None}),
                (['--venv-root'], {'help': 'root dir of venv', 'dest': 'venv', 'default': '/root/test-venv'})
            ]
        )

    def _run(self, args, extra=None):
        if not os.path.isfile(args.pkg):
            raise ZTestError('package[%s] not found' % args.pkg)

        file_name = os.path.basename(args.pkg)
        project_name = file_name.split('-', 2)[0]

        venv_dir = os.path.join(args.venv, project_name)
        if not os.path.isdir(venv_dir):
            raise ZTestError('cannot find venv folder[%s], you may want to call "zguest venv" first' % venv_dir)

        venv_activate = '%s/bin/activate' % venv_dir

        pkgs = []
        if args.deps:
            for dep in args.deps.split(','):
                dep = dep.strip()
                if not os.path.isfile(dep):
                    raise ZTestError('cannot find dependent library file[%s]' % dep)

                pkgs.append(dep)

        pkgs.append(args.pkg)

        for pkg in pkgs:
            bash.call_with_screen_output('source %s && pip install %s && deactivate' % (venv_activate, pkg))

