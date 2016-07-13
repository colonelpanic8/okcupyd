import pkg_resources

from invoke import Program

from .attractiveness_finder import AttractivenessFinder
from .photo import PhotoUploader
from .session import Session
from .statistics import Statistics
from .user import User
from . import tasks
from .util import save_file


__version__ = pkg_resources.get_distribution('okcupyd').version

@property
def always_add_task_args_initial_context(self):
    from invoke.parser import ParserContext
    args = self.core_args()
    args += self.task_args()
    return ParserContext(args=args)


def interactive():
    Program.initial_context = always_add_task_args_initial_context
    return Program(name="OKCupyd", version=__version__, namespace=tasks.ns).run()


__all__ = ('User', 'AttractivenessFinder', 'Statistics',
           'save_file', 'interactive', 'PhotoUploader', 'Session',
           '__version__')
