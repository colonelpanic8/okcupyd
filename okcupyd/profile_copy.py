import logging

from .question import Questions


log = logging.getLogger(__name__)


class Copy(object):

    copy_methods = ['questions', 'photos', 'essays']

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

    def photos(self):
        source_user_profile = self.dest_user.get_profile(self.source_user.profile.username)
        # Reverse because pictures appear in inverse chronological order.
        return [self.dest_user.photo.upload_and_confirm(info)
                for info in reversed(source_user_profile.photo_infos)]

    def essays(self):
        for essay_name in self.dest_user.profile.essays.essay_names:
            setattr(self.dest_user.profile.essays, essay_name,
                    getattr(self.source_user.profile.essays, essay_name))

    def all(self):
        for method_name in self.copy_methods:
            getattr(self, method_name)()
