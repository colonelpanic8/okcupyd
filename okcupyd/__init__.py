import argparse
import pkg_resources
import sys

from invoke import cli as invoke
import IPython

from . import tasks
from . import util
from .attractiveness_finder import AttractivenessFinder
from .photo import PhotoUploader
from .session import Session
from .statistics import Statistics
from .user import User
from .util import save_file


__version__ = pkg_resources.get_distribution('okcupyd').version


def interactive():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='store_true',
                        help='Display the version number of okcupyd')
    util.add_command_line_options(parser.add_argument)
    args = parser.parse_args()
    if args.version:
        print(__version__)
        return sys.exit()
    util.handle_command_line_options(args)
    util.get_credentials()
    u = User()
    IPython.embed()
    # try:
    #     args, collection, parser_contexts = invoke.parse(sys.argv, collection=tasks.ns)
    # except invoke.Exit as e:
    #     # 'return' here is mostly a concession to testing. Meh :(
    #     # TODO: probably restructure things better so we don't need this?
    #     return sys.exit(e.code)
    # executor = invoke.Executor(tasks.ns, invoke.Context(**invoke.derive_opts(args)))

    # _tasks = invoke.tasks_from_contexts(parser_contexts, tasks.ns)
    # dedupe = not args['no-dedupe'].value
    # executor.execute(*_tasks, dedupe=dedupe)


__all__ = ('User', 'AttractivenessFinder', 'Statistics',
           'save_file', 'interactive', 'PhotoUploader', 'Session',
           '__version__')
