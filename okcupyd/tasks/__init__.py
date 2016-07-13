import logging

from invoke import Collection
import IPython

from . import copy
from . import db as db_collection
from . import util as task_util
from okcupyd import user, db, util


log = logging.getLogger(__name__)

ns = Collection()

ns.add_collection(copy)
ns.add_collection(db_collection)
nstask = task_util.build_task_factory(ns)


@nstask(aliases='l')
def login(ctx):
    util.get_credentials()


@nstask(pre=(login,), default=True, aliases='i')
def interactive(ctx):
    u = user.User()
    u = u
    IPython.embed()


@nstask(aliases='s')
def session(ctx):
    with db.txn() as session:
        session = session
        IPython.embed()


@nstask(pre=(login,))
def enable_logger(logger_name):
    util.enable_logger(logger_name)


@nstask(aliases='c')
def credentials(ctx, module_name):
    util.update_settings_with_module(module_name)


@nstask(aliases=('eal',))
def enable_all_loggers(ctx):
    for logger_name in ('okcupyd', 'requests', __name__):
        util.enable_logger(logger_name)
    db.Session.kw['bind'].echo = True
