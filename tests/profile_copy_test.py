import mock

from . import util
from okcupyd import User


@util.use_cassette
def test_profile_questions_copy(vcr_live_sleep):
    # This could be better...
    with mock.patch('okcupyd.profile_copy.time.sleep', vcr_live_sleep):
        user = User()
        # Find a user that has answered fewer than 100 questions.
        # This is going to issue an insane number of requests if we don't do this
        for profile in user.search(join_date='week'):
            try:
                profile.questions[100]
            except IndexError:
                break
            else:
                pass
                user.copy(profile).questions()

        for question in profile.questions():
            assert question.their_answer == question.my_answer
