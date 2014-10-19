import sqlalchemy

from okcupyd import db
from okcupyd.db import model


def post_stats(user, _):
    with db.txn() as session:
        stuff = session.query(model.User, sqlalchemy.func.COUNT(model.Message.id)).join(
            model.Message,
            model.Message.sender_id == model.User.id
        ).group_by(model.Message.sender_id).order_by(sqlalchemy.func.COUNT(model.Message.id).desc()).limit(30)
    
