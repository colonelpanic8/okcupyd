from . import util
from okcupyd import User
from okcupyd.profile import Profile


@util.use_cassette
def test_unicode_in_messages_threads():
    new_user_instance = User()
    assert len(new_user_instance.inbox.items) >= 30
    assert len(new_user_instance.outbox.items) >= 30


@util.use_cassette
def test_inbox_refresh():
    User().inbox.refresh()


@util.use_cassette
def test_initiator_and_respondent():
    assert isinstance(User().inbox[0].initiator, Profile)
    assert isinstance(User().inbox[0].respondent, Profile)