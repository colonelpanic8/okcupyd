import argparse
import os
import sys

from IPython import start_ipython

from . import util

def go():
    parser = argparse.ArgumentParser()
    util.add_command_line_options(parser.add_argument)
    util.handle_command_line_options(parser.parse_args())
    util.get_credentials()
    sys.exit(start_ipython(['-i', os.path.join(os.path.dirname(__file__), 'start.py')]))


from .attractiveness_finder import AttractivenessFinder
from .photo import PhotoUploader
from .search import search
from .session import Session
from .statistics import Statistics
from .user import User
from .util import save_file


__all__ = ('search', 'User', 'AttractivenessFinder', 'Statistics',
           'save_file', 'go', 'PhotoUploader', 'Session')
