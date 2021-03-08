from ztest.core import Cmd
from utils.error import ZTestError
import os
import docker


class ExportImageCmd(Cmd):
    def __init__(self):
        super(ExportImageCmd, self).__init__(
            name='export',
            help='export an image as tar.gz file',
            args=[
                (['-t', '--tag'], {'help': 'the tag of image that is to be exported', 'dest': 'tag', 'required': True}),
                (['-o', '--output'], {'help': 'output path of tar.gz file', 'dest': 'output', 'default': None, 'required': False})
            ]
        )

        self.tag = None
        self.output = None

    def _run(self, args, extra=None):
        self.tag = args.tag
        self.output = args.output

        img = docker.find_image(self.tag)
        if img is None:
            raise ZTestError('cannot find image with tag[%s]' % self.tag)

        if self.output is None:
            output_path = ('%s_%s.tar.gz' % (img.Repository, img.Tag)).replace(':', '_')
        else:
            if self.output.endswith('tar.gz'):
                dir_name = os.path.dirname(self.output)
                file_name = os.path.basename(self.output)
            else:
                dir_name = self.output
                file_name = ('%s_%s.tar.gz' % (img.Repository, img.Tag)).replace(':', '_')

            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)

            output_path = os.path.join(dir_name, file_name)

        docker.export_image(self.tag, output_path)

        self.info('\n\nSUCCESSFULLY export the image[%s] to %s' % (self.tag, output_path))

