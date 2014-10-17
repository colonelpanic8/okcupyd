import logging
import time

from .profile import Profile
from .question import Questions


log = logging.getLogger(__name__)


class Copy(object):
    """Copy photos, essays and other attributes from one profile to another."""

    copy_methods = ['photos', 'essays', 'looking_for', 'details', 'questions']

    def __init__(self, source_profile_or_user, dest_user):
        """
        :param source_profile_or_user: A :class:`~okcupyd.user.User` or
                                       :class:`~okcupyd.profile.Profile` object
                                       from which to copy attributes.
                                       :meth:`~.Copy.questions` will not
                                       will not preserve the importance of
                                       copied questions if a
                                       :class:`~okcupyd.profile.Profile`
                                       instance is provided.
        :param dest_user: A :class:`~okcupyd.user.User` to which data will be
                          copied
        """
        if isinstance(source_profile_or_user, Profile):
            self.source_profile = source_profile_or_user
            self.source_user = None
        else:
            self.source_user = source_profile_or_user
            self.source_profile = self.source_user.profile
        self.dest_user = dest_user

    def questions(self):
        """Copy questions to the destination user. When this class was
        initialized with a :class:`~okcupyd.profile.Profile`, this will
        delete any existing questions answers on the destination account.
        """
        if self.source_user:
            return self._copy_questions_from_user()
        else:
            return self._copy_questions_from_profile()

    def _copy_questions_from_user(self):
        dest_questions = self.dest_user.questions
        for key, importance in Questions.importance_name_to_number.items():
            questions = getattr(self.source_user.questions, key)
            for question in questions:
                log.debug(
                    dest_questions.respond_from_user_question(
                        question,
                        importance
                    ).content
                )

    def _copy_questions_from_profile(self):
        # Answer all of the questions that the source user has answered.
        # So that we can see their answers
        for question in self.source_profile.questions:
            log.debug(u'Answering {0}: {1} to see {2}\'s answer'.format(
                question.id, question.text, self.source_profile.username
            ))
            if not question.answered:
                self.dest_user.questions.respond(question.id, [1], [1], 3)

        # Load all of their questions. We use a new question fetchable because
        # the one that lives on the profile has been accessed and has cached
        # data.
        source_questions = self.source_profile.question_fetchable()[:]
        log.debug(u'Copying {0} questions from {1} to {2}'.format(
            len(source_questions),
            self.source_profile.username,
            self.dest_user.username
        ))
        id_to_user_question = {question.id: question
                               for question in self.dest_user.profile.questions}
        self.dest_user.questions.clear()
        while True:
            log.debug(u'Sleeping to wait for questions to clear')
            time.sleep(5)
            try:
                question = self.dest_user.profile.question_fetchable()[0]
                log.debug(u'Destination user still has question {0}'.format(
                    question.text
                ))
            except IndexError:
                break

        for question in source_questions:
            try:
                user_question = id_to_user_question[question.id]
            except KeyError:
                log.debug(u'No user question found for {0}: {1}'.format(
                    question.id, question.text
                ))
            else:
                log.debug(u'Answering {0}: {1}'.format(
                    question.id, question.text
                ))
                self.dest_user.questions.respond_from_question(question,
                                                               user_question, 3)

    def photos(self):
        """Copy photos to the destination user."""
        # Reverse because pictures appear in inverse chronological order.
        for photo_info in self.dest_user.profile.photo_infos:
            self.dest_user.photo.delete(photo_info)
        return [self.dest_user.photo.upload_and_confirm(info)
                for info in reversed(self.source_profile.photo_infos)]

    def essays(self):
        """Copy essays from the source profile to the destination profile."""
        for essay_name in self.dest_user.profile.essays.essay_names:
            setattr(self.dest_user.profile.essays, essay_name,
                    getattr(self.source_profile.essays, essay_name))

    def looking_for(self):
        """Copy looking for attributes from the source profile to the
        destination profile.
        """
        looking_for = self.source_profile.looking_for
        return self.dest_user.profile.looking_for.update(
            gentation=looking_for.gentation,
            single=looking_for.single,
            near_me=looking_for.near_me,
            kinds=looking_for.kinds,
            ages=looking_for.ages
        )

    def details(self):
        """Copy details from the source profile to the destination profile."""
        return self.dest_user.profile.details.convert_and_update(
            self.source_profile.details.as_dict
        )

    def all(self):
        """Invoke all of :meth:`~.Copy.questions`, :meth:`~.Copy.details`,
        :meth:`~.Copy.essays`, :meth:`~.Copy.photos`, :meth:`~.Copy.looking_for`
        """
        for method_name in self.copy_methods:
            getattr(self, method_name)()
