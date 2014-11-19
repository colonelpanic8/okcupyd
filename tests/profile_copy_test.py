import mock

from . import util
from okcupyd import User
from okcupyd.profile_copy import Copy


@util.skip_if_live
@util.use_cassette
def test_profile_questions_copy(vcr_live_sleep):
    # This could be better...
    with mock.patch('okcupyd.profile_copy.time.sleep', vcr_live_sleep):
        user = User()
        # Find a user that has answered fewer than 50 questions.
        # This is going to issue an insane number of requests if we don't do this
        profile = get_profile_with_max_questions(
            user, max_questions=50
        )
        user.copy(profile).questions()

        for question in profile.questions():
            assert question.their_answer == question.my_answer


def get_profile_with_max_questions(user, max_questions=100):
    for profile in user.search(join_date='week'):
        try:
            profile.questions[max_questions]
        except IndexError:
            return profile
        else:
            pass


@util.use_cassette(match_on=util.match_on_no_body)
def test_profile_copy_smoke_test(vcr_live_sleep):
    with mock.patch('okcupyd.profile_copy.time.sleep', vcr_live_sleep):
        user = User()
        profile = get_profile_with_max_questions(user, 50)
        user.copy(profile).all()


def test_profile_photo_copy_deletes_old_photos():
    mock_dest_user = mock.Mock()
    mock_photo_info = mock.Mock(id=3)
    mock_dest_user.profile.photo_infos = [mock_photo_info]
    Copy(mock.Mock(profile=mock.Mock(photo_infos=[])), mock_dest_user).photos()
    mock_dest_user.photo.delete.assert_called_once_with(mock_photo_info)
