from . import util
from okcupyd import User


@util.use_cassette
def test_unicode_in_messages_threads():
    new_user_instance = User()
    assert len(new_user_instance.inbox) >= 30
    assert len(new_user_instance.outbox) >= 30


@util.use_cassette
def test_inbox_refresh():
    User().inbox.refresh()


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
