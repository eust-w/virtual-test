from ztest.core import Cmd
from ztest import env
from utils.error import ZTestError
import os
import docker
from utils import bash


DOCKER_IMAGE_TAG = env.env_var('ztest.docker.baseImage.tag', str, 'ztest:latest')
DOCKER_IMAGE_SOURCE_IGNORED = env.env_var('ztest.docker.baseImage.sourceIgnored', str, '.git,dist')


class InitCmd(Cmd):
    def __init__(self):
        super(InitCmd, self).__init__(
            name='init',
            help='init a test environment',
            args=[
                (['--ztest-pkg'], {'help': 'ZTest python package file', 'dest': 'ztest_pkg', 'default': None}),
                (['--image'], {'help': 'VM image for running test', 'dest': 'image', 'default': None}),
                (['--src'], {'help': 'source directory that includes code to be tested', 'dest': 'src', 'required': True})
            ]
        )

        self.ztest_pkg = None
        self.image = None
        self.src = None
        self.image_id = None
        self.container_id = None
        self.source = None

    def _find_ztest_pkg(self):
        founds = []

        for f in os.listdir('.'):
            if not os.path.isfile(f):
                continue

            if f.startswith('ztest-') and f.endswith('tar.gz'):
                founds.append(f)

        if not founds:
            raise ZTestError('cannot find any ztest python package under %s. The ztest package is like ztest-{version}.tar.gz. Please'
                             ' specify the package by --ztest-pkg option' % os.path.abspath('.'))

        if len(founds) > 1:
            raise ZTestError('found more than one ztest python package[%s] under %s. Please specify one by --ztest-pkg option' % (
                ','.join(founds), os.path.abspath('.')
            ))

        return founds[0]

    def _cleanup_old_docker_image(self):
        docker.rm_old_docker_image(DOCKER_IMAGE_TAG.value())


    def _import_image(self):
        bash.call_with_screen_output('docker load --input %s' % self.image)
        images = docker.list_images()
        for i in images:
            if '%s:%s' % (i.Repository, i.Tag) == DOCKER_IMAGE_TAG.value():
                self.image_id = i.ID
                return

        raise ZTestError('cannot find docker image[%s], the importing seems failed' % DOCKER_IMAGE_TAG.value())


    def _run_container(self):
        self.container_id = bash.call('docker run -d %s' % DOCKER_IMAGE_TAG.value()).strip('\n')


    def _create_venv(self):
        bash.call_with_screen_output('docker exec %s zguest venv' % self.container_id)


    def _install_ztest(self):
        bash.call_with_screen_output('docker cp %s %s:/root' % (self.ztest_pkg, self.container_id))
        target_path = os.path.join('/root', os.path.basename(self.ztest_pkg))
        bash.call_with_screen_output('docker exec %s pip install %s' % (self.container_id, target_path))


    def _copy_source(self):
        paths = [p for p in self.source.split('/') if p.strip()]
        if len(paths) == 1:
            source_dir_name = paths[0]
        else:
            source_dir_name = paths[-1]

        tmp_source = 'tmp-%s' % source_dir_name
        bash.call('rm -rf %s' % tmp_source)

        ignored = DOCKER_IMAGE_SOURCE_IGNORED.value().split(',')
        ignored = [i.strip() for i in ignored]
        ignored = ['--exclude "%s"' % i for i in ignored]

        if ignored:
            bash.call_with_screen_output('rsync -a %s %s %s' % (' '.join(ignored), self.source, tmp_source))
        else:
            bash.call_with_screen_output('rsync -a %s %s' % (self.source, tmp_source))

        bash.call_with_screen_output('docker cp %s %s:/root/%s' % (self.source, self.container_id, source_dir_name))

    def _validate(self):
        if not os.path.isfile(self.ztest_pkg):
            raise ZTestError('cannot find ztest python package: %s' % self.ztest_pkg)

        if not os.path.isfile(self.image):
            raise ZTestError('cannot find docker image: %s' % self.image)

        if not os.path.isdir(self.source):
            raise ZTestError('cannot find source: %s' % self.source)

    def _run(self, args, extra=None):
        if args.ztest_pkg is not None:
            self.ztest_pkg = args.ztest_pkg
        else:
            self.ztest_pkg = self._find_ztest_pkg()

        if args.image is not None:
            self.image = args.image
        else:
            self.image = self._find_image()

        self.source = args.src

        self._validate()
        self._cleanup_old_docker_image()
        self._import_image()
        self._run_container()
        self._install_ztest()
        self._copy_source()
        self._create_venv()

    def _find_image(self):
        founds = []

        for f in os.listdir('.'):
            if not os.path.isfile(f):
                continue

            if f.startswith('image-') and f.endswith('tar.gz'):
                founds.append(f)

        if not founds:
            raise ZTestError('cannot find any vm image under %s. The vm image is like ztest-{version}.tar.gz. Please'
                             ' specify the package by --image option' % os.path.abspath('.'))

        if len(founds) > 1:
            raise ZTestError('found more than one images[%s] under %s. Please specify one by --image option' % (
                ','.join(founds), os.path.abspath('.')
            ))

        return founds[0]

