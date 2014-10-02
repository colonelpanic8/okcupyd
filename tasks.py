import importlib
import logging
import time

from invoke import task
from okcupyd.attractiveness_finder import AttractivenessFinder
from okcupyd import User, db, util
from okcupyd.db import mailbox, model
from okcupyd.profile_copy import Copy


log = logging.getLogget(__name__)


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


@task
def enable_all_loggers():
    for logger_name in ('okcupyd', 'requests'):
        util.enable_logger(logger_name)
    db.Session.kw['bind'].echo = True



@task
def reset_db():
    util.enable_logger(__name__)
    log.info(db.Base.metadata.bind)
    db.Base.metadata.drop_all()
    db.Base.metadata.create_all()


@task
def sync_messages():
    user = User()
    mailbox.Sync(user).all()
    log.info(model.Messages.query(model.User.okc_id == user.id))
