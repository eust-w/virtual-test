import tempfile

from utils.logging import get_logger


logger = get_logger(__name__)

_root_dir = tempfile.mkdtemp()
logger.debug('create test root dir at: %s' % _root_dir)

