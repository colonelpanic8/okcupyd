import mock
import pytest
from sqlalchemy.orm.exc import NoResultFound

from okcupyd import db
from okcupyd.db import model


def test_integrity_error_on_okc_id_handled_by_safe_upsert():
    session = db.Session()
    other_session = db.Session()
    m1 = model.MessageThread(okc_id=1, initiator_id=1, respondent_id=1)
    m2 = model.MessageThread(okc_id=1, initiator_id=1, respondent_id=2)

    other_session.add(m1)
    find_all_no_txn = model.MessageThread.find_all_no_txn
    def commit_other_session(*args, **kwargs):
        other_session.commit()
        model.MessageThread.find_all_no_txn = find_all_no_txn
        return []
        with mock.patch.object(model.MessageThread, 'find_all_no_txn',
                               commit_other_session):
            model.MessageThread.safe_upsert([m2], id_key='okc_id')

    other_session.commit()
    session.commit()


def test_model_missing():
    with pytest.raises(NoResultFound):
        model.MessageThread.find(24)


def test_nest_txn():
    with db.txn() as session:
        session.add(model.MessageThread(okc_id=2, initiator_id=1, respondent_id=1))
        with db.txn() as nested:
            nested.add(model.MessageThread(okc_id=1, initiator_id=1, respondent_id=1))
            assert nested is not session
            session.add(model.MessageThread(okc_id=3, initiator_id=1, respondent_id=1))