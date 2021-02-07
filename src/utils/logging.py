from __future__ import absolute_import
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


def get_logger(name):
    return logging.getLogger(name)