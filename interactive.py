import os

from pyokc import *


def _debug():
    import logging
    logging.bbasicConfig(level=logging.DEBUG)


if os.environ.get('PYOKC_DEBUG'):
    _debug()


af = AttractivenessFinder()
u = User()
