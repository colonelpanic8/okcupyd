import importlib
import random
import time

from invoke import task
from okcupyd import User
from okcupyd import util
from okcupyd.attractiveness_finder import AttractivenessFinder
from okcupyd.profile_copy import Copy


@task
def copy_questions(source_credentials, dest_credentials):
    source_module = importlib.import_module(source_credentials)
    dest_module = importlib.import_module(dest_credentials)
    source_user = User.with_credentials(source_module.USERNAME,
                                        source_module.PASSWORD)
    dest_user = User.with_credentials(dest_module.USERNAME,
                                      dest_module.PASSWORD)

    Copy(source_user, dest_user).questions()


@task
def enable_logger(logger_name):
    util.enable_logger(logger_name)


@task
def credentials(module_name):
    util.update_settings_with_module(module_name)


@task
def answer_all_their_questions(username):
    user = User()
    them = user.get_profile(username)

    for question in them.questions:
        if not question.answered:
            user.questions.respond(question.id, [1], [1], 3)

    questions = them.question_fetchable()[:]
    print len(questions)
    question_id_to_question = {question.id: question
                               for question in user.profile.questions}
    user.questions.clear()
    time.sleep(10)
    for question in questions:
        user.questions.respond_from_question(question,
                                             question_id_to_question, 3)


@task
def rate_attractive_girls():
    user = User()
    af = AttractivenessFinder(user._session)
    while True:
        p = user.quickmatch()
        if af(p.username) >= 7000:
            p.rate(5)
