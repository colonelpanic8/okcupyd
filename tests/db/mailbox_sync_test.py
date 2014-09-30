import mock
import pytest

from .. import util
from okcupyd import User
from okcupyd.db import mailbox_sync, model, txn


@pytest.fixture
def mock_user():
    mock_user = mock.MagicMock()
    return mock_user


@pytest.fixture
def inbox_sync(mock_user):
    return mailbox_sync.MailboxSyncer(mock_user.inbox)


def set_inbox(inbox, value):
    inbox.__iter__ = value.__iter__
    inbox.items = value
    inbox.refresh.return_value = value


def test_mailbox_sync_creates_message_rows(T, inbox_sync, mock_user):
    initiator_one = 'first_initiator'
    respondent_one = 'respondent_one'
    respondent_two = 'respondent_two'
    initiator_two = 'other'
    set_inbox(mock_user.inbox, [
        T.build_mock.thread(initiator=initiator_one, respondent=respondent_one),
        T.build_mock.thread(initiator=initiator_one, respondent=respondent_two),
        T.build_mock.thread(initiator=initiator_two, respondent=respondent_two,
                            message_count=1)
    ])

    id_to_mock_thread = {t.id: t for t in mock_user.inbox.items}

    inbox_sync.sync()
    mock_user.inbox.refresh.assert_called_once_with()

    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        assert len(message_threads) == len(id_to_mock_thread)
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.id]
            )

    # Sync again and make sure that nothing has been updated.
    inbox_sync.sync()
    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        assert len(message_threads) == len(id_to_mock_thread)
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.okc_id]
            )

    # Add messages to existing threads
    mock_user.inbox.items[0].messages.append(T.build_mock.message(
        sender=respondent_one, recipient=initiator_one, content='final'
    ))

    mock_user.inbox.items[2].messages.append(T.build_mock.message(
        sender=initiator_two, recipient=respondent_two, content='last'
    ))

    # Sync and make sure that only the new messages appear.
    inbox_sync.sync()
    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        assert len(message_threads) == len(id_to_mock_thread)
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.okc_id]
            )

    # Add a new message thread and make sure that only it appears.
    set_inbox(mock_user.inbox, [
        T.build_mock.thread(initiator=initiator_one,
                            respondent=initiator_two)
    ] + mock_user.inbox.items)

    id_to_mock_thread = {t.id: t for t in mock_user.inbox.items}
    inbox_sync.sync()

    with txn() as session:
        message_threads = session.query(model.MessageThread).all()
        for message_thread in message_threads:
            T.ensure.thread_model_resembles_okcupyd_thread(
                message_thread,
                id_to_mock_thread[message_thread.okc_id]
            )

@util.use_cassette
def test_mailbox_sync_integration():
    user = User()
    user.quickmatch().message('test... sorry.')

    mailbox_sync.MailboxSyncer(user.outbox).sync()

    user_model = model.User.find(user.profile.id, id_key='okc_id')
    messages = model.Message.query(
        model.Message.sender_id == user_model.id
    )

    mailbox_sync.MailboxSyncer(user.outbox).sync()

    assert len(messages) == len(model.Message.query(
        model.Message.sender_id == user_model.id
    ))