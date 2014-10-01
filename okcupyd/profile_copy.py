import logging

from .question import Questions


log = logging.getLogger(__name__)


class Copy(object):

    def __init__(self, source_user, dest_user):
        self.source_user = source_user
        self.dest_user = dest_user

    def questions(self):
        dest_questions = self.dest_user.questions
        for key, importance in Questions.importance_name_to_number.items():
            questions = getattr(self.source_user.questions, key)
            for question in questions:
                log.debug(
                    dest_questions.respond_from_user_question(question,
                                                              importance).content
                )
