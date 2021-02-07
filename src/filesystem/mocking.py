from mock import patch, MagicMock
from core import _root_dir
import os

_filesystem_mocks = {}


def _mock_open():
    origin_open = open

    def side_effect(*args, **kwargs):
        # if len(args):
        #     args = list(args)
        #     args[0] = unicode(args[0])
        #     args = tuple(args)

        args = list(args)
        args[0] = os.path.join(_root_dir, args[0])
        args = tuple(args)

        return origin_open(*args, **kwargs)

    m = MagicMock(side_effect=side_effect)

    p = patch('__builtin__.open', new=m)
    p.side_effect = side_effect
    return p


def start():
    _filesystem_mocks['open'] = _mock_open()

    for _, p in _filesystem_mocks.items():
        p.start()
