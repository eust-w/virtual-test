import docker
from utils import bash
from env import env_var
from utils.logging import get_logger

BASE_IMAGE_TAG = env_var('ztest.baseimage.tag', str, 'pyut:0.1')
BASE_IMAGE_SOURCE_ROOT = env_var('ztest.baseimage.sourceroot', str, '/root')

logger = get_logger(__name__)


class PrepareImage(object):
    def __init__(self, base_image_path, source_dir):
        self.docker = docker.from_env()
        self.base_image_path = base_image_path
        self.source_dir = source_dir
        self.container = None

    def _import_base_image_to_docker(self):
        '''

        :param base_image_path: path to base image
        :return:
        '''
        logger.debug('importing base image: %s' % self.base_image_path)
        bash.call('docker load --input %s' % self.base_image_path)

    def _start_base_image_container(self):
        self.container = self.docker.containers.run(BASE_IMAGE_TAG.name, detach=True)

    def _copy_source_code_to_container(self):
        logger.debug('copying source folder into the container[%s]' % self.container.short_id)
        bash.call('docker cp %s %s:%s' % (self.source_dir, self.container.short_id, BASE_IMAGE_SOURCE_ROOT.value()))

