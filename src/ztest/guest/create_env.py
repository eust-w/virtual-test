import tempfile

from ztest.core import Cmd
from utils.error import ZTestError
from utils import bash
import os.path
import distutils.core


class CreateVenv(Cmd):
    def __init__(self):
        super(CreateVenv, self).__init__(
            name='venv',
            help='create venv for sub-projects',
            prog='zguest venv [options]',
            args=[
                (['--src'], {'help': 'source directory', 'dest': 'src', 'default': '/root/zstack-utility', 'required': True}),
                (['--dst'], {'help': 'dest directory where venv for sub-projects to be created', 'dest': 'dst', 'default':'/root/test-venv'})
            ]
        )

    def _create_requirement_txt(self, sub_project_path, setup_py):
        req_file_fd, req_file_path = tempfile.mkstemp()
        setup = distutils.core.run_setup(setup_py)
        reqs = setup.install_requires
        reqs.append('pytest') # install for unit test

        test_req_file = '%s/test_requirements.txt' % sub_project_path
        if os.path.isfile(test_req_file):
            with open(test_req_file, "r") as fd:
                txt = fd.read()
                for line in txt.split('\n'):
                    line = line.strip(' \t\n\r')
                    if line:
                        reqs.append(line)

        os.write(req_file_fd, '\n'.join(reqs))
        os.close(req_file_fd)
        return req_file_path

    def _run(self, args, extra=None):
        bash.call('rm -rf %s' % args.dst)
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
            venv_activate = '%s/bin/activate' % venv_dir
            bash.call_with_screen_output('virtualenv %s' % venv_dir)

            req_txt_file = self._create_requirement_txt(sub_project_path, setup_py)
            bash.call_with_screen_output('source %s && pip install -r %s && deactivate' % (venv_activate, req_txt_file))
            bash.call('mv %s %s' % (req_txt_file, venv_dir))
            self.info('Created venv: %s' % venv_dir)


