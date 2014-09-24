from . import util
from okcupyd import User
from okcupyd.profile import Essays


@util.use_cassette('user_no_picture')
def test_handle_no_pictures():
    assert isinstance(User().username, str)


@util.use_cassette('user_get_threads')
def test_get_inbox():
    user = User()
    assert len(user.inbox.items) == 1

    for message_thread in user.inbox:
        for message in message_thread.messages:
            assert hasattr(message, 'sender')


@util.use_cassette('access_profile_from_message_thread')
def test_message_thread_to_profile():
    profile = User().inbox[0].correspondent_profile
    assert profile.age
    assert profile.age > 18
    assert isinstance(profile.rating, int)


@util.use_cassette('user_count')
def test_user_search_count():
    assert len(User().search(count=1)) == 1


@util.use_cassette('test_user_essays')
def test_user_essays():
    user = User()
    first_essay = 'an essay'
    user.essays.self_summary = first_essay
    assert user.essays.self_summary == first_essay

    second_essay = 'next_essay'
    user.essays.self_summary = second_essay

    assert user.essays.self_summary == second_essay


@util.use_cassette('test_user_essays_refresh')
def test_user_essay_refresh():
    # Test Refresh Function
    user = User()
    user2 = User(user._session)
    user.self_summary = 'other stuff'

    user2.essays.refresh()
    assert user.essays.self_summary == user2.essays.self_summary
