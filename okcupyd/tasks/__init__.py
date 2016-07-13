import logging

from invoke import Collection, task
import IPython

from . import copy
from . import db as db_collection
from okcupyd import user, db, util


log = logging.getLogger(__name__)

ns = Collection()
ns.add_collection(copy)
ns.add_collection(db_collection)

login = task(lambda ctx : util.get_credentials())
ns.add_task(login, 'login')


@ns.add_task
@task(login, default=True)
def interactive(ctx):
    u = user.User()
    u = u
    IPython.embed()


@ns.add_task
@task(aliases='s')
def session(ctx):
    with db.txn() as session:
        session = session
        IPython.embed()


@ns.add_task
@task(login)
def enable_logger(logger_name):
    util.enable_logger(logger_name)


@ns.add_task
@task(aliases=('c',))
def credentials(ctx, module_name):
    util.update_settings_with_module(module_name)


@ns.add_task
@task(aliases=('eal',))
def enable_all_loggers(ctx):
    for logger_name in ('okcupyd', 'requests', __name__):
        util.enable_logger(logger_name)
    db.Session.kw['bind'].echo = True
