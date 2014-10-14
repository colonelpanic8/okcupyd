import time

from invoke import task

from okcupyd import User


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
    while True:
        p = user.quickmatch()
        if user.attractiveness_finder(p.username) >= 7000:
            p.rate(5)
