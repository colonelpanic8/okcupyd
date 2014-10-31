from okcupyd import User

from . import util


@util.use_cassette
def test_question_answer_id_for_user_question():
    user = User()
    user_question = user.profile.questions[0]
    assert isinstance(user_question.answer_id, int)
    assert user_question.answer_id == user.get_question_answer_id(user_question)


@util.use_cassette
def test_question_answer_id_for_profile_question():
    user = User()
    assert isinstance(user.get_question_answer_id(user.quickmatch().questions[0]), int)
