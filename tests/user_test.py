from . import util
from pyokc import User


@util.use_cassette('user_no_picture')
def test_handle_no_pictures():
    assert User().username == util.TESTING_USERNAME


@util.use_cassette('user_get_threads')
def test_get_inbox():
    user = User()
    assert len(user.inbox.items) == 1

    for message_thread in user.inbox:
        for message in message_thread.messages:
            assert hasattr(message, 'sender')
