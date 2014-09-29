from . import util
from okcupyd import User


@util.use_cassette
def test_unicode_in_messages_threads():
    new_user_instance = User()
    assert len(new_user_instance.inbox.items) >= 30
    assert len(new_user_instance.outbox.items) >= 30


@util.use_cassette
def test_inbox_refresh():
    User().inbox.refresh()