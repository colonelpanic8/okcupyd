import sys

from invoke import cli as invoke

from . import tasks
from .attractiveness_finder import AttractivenessFinder
from .photo import PhotoUploader
from .search import search
from .session import Session
from .statistics import Statistics
from .user import User
from .util import save_file


def run_invoke():
    try:
        args, collection, parser_contexts = invoke.parse(sys.argv, collection=tasks.ns)
    except invoke.Exit as e:
        # 'return' here is mostly a concession to testing. Meh :(
        # TODO: probably restructure things better so we don't need this?
        return sys.exit(e.code)
    executor = invoke.Executor(tasks.ns, invoke.Context(**invoke.derive_opts(args)))

    _tasks = invoke.tasks_from_contexts(parser_contexts, tasks.ns)
    dedupe = not args['no-dedupe'].value
    executor.execute(*_tasks, dedupe=dedupe)


__all__ = ('search', 'User', 'AttractivenessFinder', 'Statistics',
           'save_file', 'run_invoke', 'PhotoUploader', 'Session')
