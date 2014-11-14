import os

import mock
import pytest

from . import util
from okcupyd import User
from okcupyd import helpers
from okcupyd.profile import Profile


@util.use_cassette(cassette_name='user_no_picture')
def test_handle_no_pictures():
    username = User().profile.username
    assert username is not None


@util.use_cassette(cassette_name='access_profile_from_message_thread')
def test_message_thread_to_profile():
    profile = User().inbox[0].correspondent_profile
    assert profile.age
    assert profile.age > 18
    assert isinstance(profile.rating, int)


@util.use_cassette(cassette_name='user_count')
def test_user_search_count():
    assert len(User().search(count=1)) == 1


@util.use_cassette(cassette_name='test_user_essays')
def test_user_essays():
    user = User()
    first_essay = 'an essay'
    user.profile.essays.self_summary = first_essay
    assert user.profile.essays.self_summary == first_essay

    second_essay = 'next_essay'
    user.profile.essays.self_summary = second_essay

    assert user.profile.essays.self_summary == second_essay


@util.use_cassette(cassette_name='test_user_essays_refresh')
def test_user_essay_refresh():
    # Test Refresh Function
    user = User()
    user2 = User(user._session)
    user.message_me_if = 'other stuff'

    user2.profile.essays.refresh()
    assert user.profile.essays.message_me_if == (
        user2.profile.essays.message_me_if
    )


@util.use_cassette(cassette_name='visitors_test')
@util.skip_if_live
def test_visitors():
    user = User()
    assert isinstance(user.visitors[0], Profile)
    # If the user has more than one page of visitors, this ensures that
    assert isinstance(user.visitors[-1], Profile)
    assert len(user.visitors) > 26


@pytest.mark.skipif(bool(os.environ.get('CI')), reason="Unicode issues...")
@util.use_cassette(cassette_name='profile_titles')
def test_profile_titles():
    user = User()
    for essay_name in user.profile.essays.essay_names:
        setattr(user.profile.essays, essay_name, 'updated')

    expected_names_dict = {
        'favorites': 'Favorite books, movies, shows, music, and food',
        'friday_night': 'On a typical Friday night I am',
        'good_at': u'I\u2019m really good at',
        'message_me_if': 'You should message me if',
        'my_life': u'What I\u2019m doing with my life',
        'people_first_notice': (
            'The first things people usually notice about me'
        ),
        'private_admission': (
            u'The most private thing I\u2019m willing to admit'
        ),
        'self_summary': 'My self-summary',
        'six_things': 'The six things I could never do without',
        'think_about': 'I spend a lot of time thinking about'
    }

    expected_names_dict = {key: helpers.replace_chars(value)
                           for key, value in expected_names_dict.items()}

    assert user.profile.essays.short_name_to_title == expected_names_dict


@util.use_cassette
def test_user_profile_attributes():
    user_profile = User().profile
    assert user_profile.id > 0
    assert user_profile.rating == 0


@util.use_cassette
def test_logged_in_users_photos():
    user = User()
    assert len(user.profile.photo_infos) > 0


@util.use_cassette
def test_user_message():
    user = User()
    message_info = user.message(user.quickmatch().username,
                                'abcdefghijklmnopqrstuvwxyz')
    assert message_info.thread_id != None
    assert int(message_info.message_id) > 0


@util.use_cassette
def test_user_delete_threads():
    user = User()
    message_info = user.message(user.quickmatch().username,
                                'abcdefghijklmnopqrstuvwxyz')
    assert message_info.thread_id != None
    user.delete_threads(user.outbox())
    assert user.outbox()[:] == []


@util.use_cassette
def test_user_get_user_question():
    user = User()
    profile = user.quickmatch()
    question = profile.questions[0]
    user_question = user.get_user_question(question)
    assert question.id == user_question.id
    assert question.text == user_question.text
    assert 0 < user_question.answer_id < 5
    assert 0 < user_question.get_answer_id_for_question(question) < 5


@mock.patch('okcupyd.user.time')
def test_log_path_for_user_question_not_found(mock_time):
    mock_time.time.return_value = 2
    user = User(mock.Mock())
    with mock.patch('okcupyd.profile.Profile.find_question',
                    return_value=None):
        user.get_user_question(mock.Mock())
    assert mock_time.sleep.call_count


@mock.patch('okcupyd.user.User.get_user_question')
def test_get_question_answer_id_calls_get_user_question(mock_get_user_question):
    user = User(mock.Mock())
    user.get_question_answer_id(mock.Mock(spec=['id']))
    assert mock_get_user_question.call_count
