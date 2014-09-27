import argparse
import os
import pkg_resources
import sys

from IPython import start_ipython

from . import util

def parse_args_and_run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='store_true',
                        help='Display the version number of okcupyd')
    util.add_command_line_options(parser.add_argument)
    args = parser.parse_args()
    if args.version:
        print(pkg_resources.get_distribution('okcupyd').version)
        sys.exit()
    util.handle_command_line_options(args)
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
           'save_file', 'parse_args_and_run', 'PhotoUploader', 'Session')
