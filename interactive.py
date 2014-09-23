import argparse
import os
import sys

from IPython import start_ipython

from okcupyd import util


def go():
    parser = argparse.ArgumentParser()
    util.add_command_line_options(parser.add_argument)
    util.handle_command_line_options(parser.parse_args())
    util.get_credentials()
    sys.exit(start_ipython(['-i', os.path.join('examples', 'start.py')]))


if __name__ == '__main__':
    go()
