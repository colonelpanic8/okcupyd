import datetime

import mock
import pytest

from .. import util
from okcupyd import User
from okcupyd.db import model, txn
from okcupyd.db.mailbox_sync import MailboxSyncer
from okcupyd.util import Fetchable


@pytest.fixture
def mock_user(T):
    mock_user = mock.MagicMock(
        profile=T.build_mock.profile(),
        inbox=Fetchable(mock.Mock(fetch=lambda: (i for i in range(0)))),
        outbox=Fetchable(mock.Mock(fetch=lambda: (i for i in range(0))))
    )
    return mock_user


@pytest.fixture
def mailbox_sync(mock_user):
    return MailboxSyncer(mock_user)


def set_mailbox(mailbox, value):
    def fetch():
        for i in value:
            yield i
    mailbox._fetcher.fetch = fetch
    mailbox()

@pytest.mark.skipif(True, reason='Test needs work')
def test_mailbox_sync_creates_message_rows(T, mailbox_sync, mock_user):
    T.factory.okcupyd_user(mock_user)
    initiator_one = 'first_initiator'
    respondent_one = 'respondent_one'
    respondent_two = 'respondent_two'
    initiator_two = 'other'
    inbox_items = [
        T.build_mock.thread(initiator=initiator_one, respondent=respondent_one,
                            datetime=datetime.datetime(year=2014, day=2, month=5)),
        T.build_mock.thread(initiator=initiator_one, respondent=respondent_two,
                            datetime=datetime.datetime(year=2014, day=2, month=5)),
        T.build_mock.thread(initiator=initiator_two, respondent=respondent_two,
                            datetime=datetime.datetime(year=2014, day=2, month=5),
                            message_count=1)
    ]
    set_mailbox(mock_user.inbox, inbox_items)

    id_to_mock_thread = {t.id: t for t in mock_user.inbox}

    mailbox_sync.sync()

    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        assert len(message_threads) == len(id_to_mock_thread)
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.id]
            )

    # Sync again and make sure that nothing has been updated.
    mailbox_sync.sync()
    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        assert len(message_threads) == len(id_to_mock_thread)
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.okc_id]
            )

    # Add messages to existing threads
    mock_user.inbox[0].messages.append(T.build_mock.message(
        sender=respondent_one, recipient=initiator_one, content='final'
    ))

    mock_user.inbox[2].messages.append(T.build_mock.message(
        sender=initiator_two, recipient=respondent_two, content='last'
    ))

    # Sync and make sure that only the new messages appear.
    mailbox_sync.sync()
    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        assert len(message_threads) == len(id_to_mock_thread)
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.okc_id]
            )

    # Add a new message thread and make sure that only it appears.
    set_mailbox(mock_user.inbox, [
        T.build_mock.thread(initiator=initiator_one,
                            respondent=initiator_two)
    ] + mock_user.inbox.items)

    id_to_mock_thread = {t.id: t for t in mock_user.inbox.items}
    mailbox_sync.sync()

    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.okc_id]
            )


@util.use_cassette
def test_mailbox_sync_integration(T):
    user = User()
    T.factory.okcupyd_user(user)
    user.quickmatch().message('test... sorry.')

    MailboxSyncer(user).sync()

    user_model = model.User.find(user.profile.id, id_key='okc_id')
    messages = model.Message.query(
        model.Message.sender_id == user_model.id
    )

    MailboxSyncer(user).sync()

    assert len(messages) == len(model.Message.query(
        model.Message.sender_id == user_model.id
    ))
