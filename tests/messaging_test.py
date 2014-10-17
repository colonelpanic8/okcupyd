from . import util
from okcupyd import User


@util.use_cassette
def test_message_thread_detect_deletion():
    message_thread = User().inbox[0]
    assert message_thread.with_deleted_user
    sent_thread = User().outbox[0]
    assert not sent_thread.with_deleted_user


@util.use_cassette
def test_initiator_and_respondent():
    user = User()
    their_profile = user.quickmatch()
    message_info = their_profile.message('initiated contact')
    while message_info.message_id is None:
        their_profile = user.quickmatch()
        message_info = their_profile.message('initiated contact')

    message_thread = user.outbox[0]

    assert message_thread.initiator.username == user.profile.username
    assert message_thread.respondent.username == their_profile.username
    assert message_thread.correspondent_id == their_profile.id


@util.use_cassette
def test_load_messages_on_message_thread():
    user = User()
    content = 'a message was sent'
    their_profile = user.quickmatch()
    message_info = their_profile.message(content)
    while message_info.message_id is None:
        their_profile = user.quickmatch()
        message_info = their_profile.message(content)

    assert len(user.outbox[0].messages) == 1
    assert user.outbox[0].messages[0].content == content


@util.use_cassette
def test_reply():
    user = User()
    user.quickmatch().message('test')
    message_info = user.inbox[0].reply('reply')
    assert message_info.thread_id is not None
    assert int(message_info.message_id) > 0


@util.use_cassette
def test_delete(vcr_live_sleep):
    user = User()
    their_profile = user.quickmatch()
    message_info = their_profile.message('text')
    assert message_info.thread_id != None
    thread_id = user.outbox[0].id
    user.outbox[0].delete()
    user.outbox()
    try:
        assert user.outbox[0].id != thread_id
    except IndexError:
        pass
