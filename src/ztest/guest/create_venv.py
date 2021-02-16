import distutils.core
import os.path

from utils import bash
from utils.error import ZTestError
from ztest.core import Cmd


class VenvGenerator(object):
    def __init__(self, venv_dir, sub_project_path, setup_py):
        self.sub_project_path = sub_project_path
        self.setup_py = setup_py
        self.venv_dir = venv_dir
        self.venv_activate = '%s/bin/activate' % self.venv_dir
        self.exists = os.path.isdir(venv_dir)
        self.new_reqs = None
        self.req_file = os.path.join(self.venv_dir, 'requirements.txt')

    def _generate_new_req_list(self):
        setup = distutils.core.run_setup(self.setup_py)
        reqs = setup.install_requires
        reqs.append('pytest')  # install for unit test

        test_req_file = '%s/test_requirements.txt' % self.sub_project_path
        if os.path.isfile(test_req_file):
            with open(test_req_file, "r") as fd:
                txt = fd.read()
                for line in txt.split('\n'):
                    line = line.strip(' \t\n\r')
                    if line:
                        reqs.append(line)

        reqs.sort()
        return reqs

    def _do_generate(self):
        base_dir = os.path.dirname(self.venv_dir)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)

        bash.call_with_screen_output('virtualenv %s' % self.venv_dir)

        if self.new_reqs is None:
            self.new_reqs = self._generate_new_req_list()

        with open(self.req_file, 'w+') as fd:
            fd.write('\n'.join(self.new_reqs))

        bash.call_with_screen_output('source %s && pip install -r %s && deactivate' % (self.venv_activate, self.req_file))
        Cmd.info('Created venv: %s' % self.venv_dir)

    def test_venv(self):
        if not os.path.isfile(self.venv_activate):
            return False

        r, _, _ = bash.run('source %s && deactivate' % self.venv_activate)
        if r != 0:
            return False

        return True

    def generate(self):
        if not self.test_venv():
            # the venv broken, delete it
            bash.call_with_screen_output('rm -rf %s' % self.venv_dir)

        self._do_generate()


class CreateVenv(Cmd):
    def __init__(self):
        super(CreateVenv, self).__init__(
            name='venv',
            help='update/create venv for sub-projects',
            prog='zguest venv [options]',
            args=[
                (['--src'], {'help': 'source directory', 'dest': 'src', 'default': '/root/zstack-utility'}),
                (['--dst'], {'help': 'dest directory where venv for sub-projects to be created', 'dest': 'dst', 'default':'/root/test-venv'}),
                (['--recreate'], {'help': 'delete the --dst and recreate all venv', 'dest': 'recreate', 'action': 'store_true', 'default': False})
            ]
        )

    def _run(self, args, extra=None):
        if args.recreate:
            bash.call('rm -rf %s' % args.dst)

        if not os.path.exists(args.dst):
            os.makedirs(args.dst)

        if not os.path.isdir(args.src):
            raise ZTestError('source directory[%s] not found' % args.src)

        sub_projects = []

        for sub in os.listdir(args.src):
            sub_project_path = os.path.join(args.src, sub)
            if not os.path.isdir(sub_project_path):
                continue

            setup_py = os.path.join(sub_project_path, 'setup.py')
            if not os.path.isfile(setup_py):
                continue

            sub_projects.append((sub, sub_project_path, setup_py))

        for sub, sub_project_path, setup_py in sub_projects:
            venv_dir = os.path.join(args.dst, sub)
            VenvGenerator(venv_dir, sub_project_path, setup_py).generate()


