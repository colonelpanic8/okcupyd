import logging

from invoke import Collection, task
import IPython

from . import copy
from . import db as db_collection
from okcupyd import user, db, util
from okcupyd.db import model


log = logging.getLogger(__name__)


ns = Collection()
ns.add_collection(copy)
ns.add_collection(db_collection)

login = task(util.get_credentials)
ns.add_task(login, 'login')


@ns.add_task
@task(login, default=True)
def interactive():
    u = user.User()
    IPython.embed()

@ns.add_task
@task(aliases='s')
def session():
    with db.txn() as session:
        IPython.embed()


@ns.add_task
@task(login)
def enable_logger(logger_name):
    util.enable_logger(logger_name)


@ns.add_task
@task(aliases=('c',))
def credentials(module_name):
    util.update_settings_with_module(module_name)


@ns.add_task
@task(aliases=('eal',))
def enable_all_loggers():
    for logger_name in ('okcupyd', 'requests', __name__):
        util.enable_logger(logger_name)
    db.Session.kw['bind'].echo = True


