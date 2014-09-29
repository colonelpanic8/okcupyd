from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from okcupyd.db import model, with_txn


def have_messaged_by_username_no_txn(session, username_one, username_two):
    user_one = aliased(model.User)
    user_two = aliased(model.User)
    return session.query(model.MessageThread).\
        join(user_one, user_one.id == model.MessageThread.initiator_id).\
        join(user_two, user_two.id == model.MessageThread.respondent_id).\
        filter(or_(
            and_(user_one.handle == username_one, user_two.handle == username_two),
            and_(user_one.handle == username_two, user_two.handle == username_one),
        )).exists()


@with_txn
def have_messaged_by_username(session, username_one, username_two):
    return session.query(
        have_messaged_by_username_no_txn(session, username_one, username_two)
    ).scalar()