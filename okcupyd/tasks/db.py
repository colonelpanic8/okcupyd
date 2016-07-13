import logging

from invoke import task
import IPython

from okcupyd import db
from okcupyd import util
from okcupyd.db import mailbox, model
from okcupyd.user import User


log = logging.getLogger(__name__)


@task(default=True)
def session(ctx):
    with db.txn() as session:
        IPython.embed()


@task
def reset(ctx):
    util.enable_logger(__name__)
    log.info(db.Base.metadata.bind)
    db.Base.metadata.drop_all()
    db.Base.metadata.create_all()


@task
def sync(ctx):
    user = User()
    mailbox.Sync(user).all()
    log.info(model.Message.query(model.User.okc_id == user.profile.id))


@task
def make(ctx):
    user = User()
    user_model = model.User.from_profile(user.profile)
    user_model.upsert_model(id_key='okc_id')
    okcupyd_user = model.OKCupydUser(user_id=user_model.id)
    okcupyd_user.upsert_model(id_key='user_id')
    return okcupyd_user
