import os

from pyokc import *


def _debug():
    import logging
    logging.basicConfig(level=logging.DEBUG)


if os.environ.get('PYOKC_DEBUG'):
    _debug()


af = AttractivenessFinder()
u = User()
