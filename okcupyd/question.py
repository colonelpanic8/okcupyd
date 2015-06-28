import functools
import logging

from . import util
from .xpath import xpb


log = logging.getLogger(__name__)


class BaseQuestion(object):
    """The abstract base class of :class:`~.Question` and
    :class:`~.UserQuestion`. Contains all the shared functionality of the
    aforementined classes. The two are quite different in some ways and can
    not always be used interchangably. See their respective docstrings for more
    details.
    """

    def __init__(self, question_element):
        self._question_element = question_element

    @property
    def answered(self):
        return 'not_answered' not in self._question_element.attrib['class']

    @util.cached_property
    def id(self):
        """
        :returns: The integer id given to this question by okcupid.com.
        """
        return int(self._question_element.attrib['data-qid'])

    _text_xpb = xpb.div.with_class('qtext').p

    @util.cached_property
    def text(self):
        return self._text_xpb.get_text_(self._question_element).strip()

    def __repr__(self):
        return u'<{1}: {0}>'.format(self.text, type(self).__name__)


class Question(BaseQuestion):
    """Represent a question answered by a user other than the logged in user.

    Note: Because of the way that okcupid presents question data it is actually
    not very easy to get the index of the answer to a question that belongs
    to a user other than the logged in user. It is possible to retrieve
    this value (see :meth:`okcupyd.user.User.get_question_answer_id` and
    :meth:`~.UserQuestion.get_answer_id_for_question`), but it
    can take quite a few requests to do so. For this reason, the answer_id is
    NOT included as an attribute on this object, despite its inclusion in
    :class:`~.UserQuestion`.
    """

    def return_none_if_unanswered(function):
        @functools.wraps(function)
        def wrapped(self):
            if self.answered:
                return function(self)
        return wrapped

    _answers_xpb = xpb.div.with_class('answers').\
                   p.with_class('answer')

    def __init__(self, question_element):
        super(Question, self).__init__(question_element)
        try:
            self._their_answer_span, self._my_answer_span = (
                self._answers_xpb.span.with_class('text').apply_(
                    self._question_element
                )
            )
            self._their_note_span, self._my_note_span = (
                self._answers_xpb.span.with_class('note').apply_(
                    self._question_element
                )
            )
        except:
            pass

    @util.cached_property
    @return_none_if_unanswered
    def their_answer(self):
        """The answer that the user whose :class:`~okcupyd.profile.Profile` this
        question was retrieved from provided to this
        :class:`~okcupyd.question.Question`.
        """
        return self._their_answer_span.text_content().strip()

    @util.cached_property
    @return_none_if_unanswered
    def my_answer(self):
        """The answer that the user whose :class:`~okcupyd.session.Session` was
        used to create this :class:`~okcupyd.question.Question` provided.
        """
        return self._my_answer_span.text_content().strip()

    @util.cached_property
    @return_none_if_unanswered
    def their_answer_matches(self):
        """
        :returns: whether or not the answer provided by the user
                  answering the question is acceptable to the logged in user.
        :rtype: rbool
        """
        return 'not_accepted' not in self._their_answer_span.attrib['class']

    @util.cached_property
    @return_none_if_unanswered
    def my_answer_matches(self):
        """
        :returns: bool indicating whether or not the answer provided
                  by the logged in user is acceptable to the user
                  answering the question.
        """
        return 'not_accepted' not in self._my_answer_span.attrib['class']

    @util.cached_property
    @return_none_if_unanswered
    def their_note(self):
        """
        :returns: The note the answering user provided as explanation for their
                  answer to this question.
        """
        return self._their_note_span.text_content().strip()

    @util.cached_property
    @return_none_if_unanswered
    def my_note(self):
        """
        :returns: The note the logged in user provided as an explanation for
                  their answer to this question.
        """
        return self._my_note_span.text_content().strip()

    _explanation_xpb = xpb.div.span.with_class('note')
    del return_none_if_unanswered


class UserQuestion(BaseQuestion):
    """Represent a question answered by the logged in user."""

    _answer_option_xpb = xpb.ul.with_class('self_answers').li
    _explanation_xpb = xpb.div.with_class('your_explanation').\
                       p.with_class('value')

    def get_answer_id_for_question(self, question):
        """Get the answer_id corresponding to the answer given for question
        by looking at this :class:`~.UserQuestion`'s answer_options.
        The given :class:`~.Question` instance must have the same id as this
        :class:`~.UserQuestion`.

        That this method exists is admittedly somewhat weird. Unfortunately, it
        seems to be the only way to retrieve this information.
        """
        assert question.id == self.id
        for answer_option in self.answer_options:
            if answer_option.text == question.their_answer:
                return answer_option.id

    @util.cached_property
    def answer_id(self):
        for answer_option in self.answer_options:
            if answer_option.is_users:
                return answer_option.id

    @util.cached_property
    def answer_options(self):
        """
        :returns: A list of :class:`~.AnswerOption` instances representing the
                  available answers to this question.
        """
        return [
            AnswerOption(element)
            for element in self._answer_option_xpb.apply_(
                self._question_element
            )
        ]

    @util.cached_property
    def explanation(self):
        """
        :returns: The explanation written by the logged in user for this
                  question (if any).
        """
        try:
            return self._explanation_xpb.get_text_(self._question_element)
        except:
            pass

    @util.cached_property
    def answer_text_to_option(self):
        return {option.text: option for option in self.answer_options}

    @util.cached_property
    def answer(self):
        """
        :returns: A :class:`~.AnswerOption` instance corresponding to the answer
                  the user gave to this question.
        """
        for answer_option in self.answer_options:
            if answer_option.is_users:
                return answer_option


class AnswerOption(object):

    def __init__(self, option_element):
        self._element = option_element

    @util.cached_property
    def is_users(self):
        """
        :returns: Whether or not this was the answer selected by the logged in
                  user.
        """
        return 'mine' in self._element.attrib['class']

    @util.cached_property
    def is_match(self):
        """
        :returns: Whether or not this was the answer is acceptable to the logged
                  in user.
        """
        return 'match' in self._element.attrib['class']

    @util.cached_property
    def text(self):
        """
        :returns: The text of this answer.
        """
        return self._element.text_content().strip()

    @util.cached_property
    def id(self):
        """
        :returns: The integer index associated with this answer.
        """
        return int(self._element.attrib['id'].split('_')[-1])

    def __repr__(self):
        return '<{0}: "{1}" (is_users={2}, is_match={3})>'.format(
            type(self).__name__,
            self.text,
            self.is_users,
            self.is_match
        )


importances = ('not_important', 'little_important', 'somewhat_important',
               'very_important', 'mandatory')


class Questions(object):
    """Interface to accessing and answering questions belonging to the logged
    in user."""

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-encoding': 'gzip,deflate',
        'accept-language': 'en-US,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.okcupid.com',
        'referer': 'https://www.okcupid.com/questions',
        'x-requested-with': 'XMLHttpRequest',
    }

    #: Human readable importance name to integer used to represent them on
    #: okcupid.com
    importance_name_to_number = {
        'mandatory': 0,
        'very_important': 1,
        'somewhat_important': 3,
        'little_important': 4,
        'not_important': 5
    }

    path = 'questions/ask'

    def __init__(self, session, importances=importances, user_id=None):
        self.importance_name_to_fetchable = {}
        for importance in importances:
            fetchable = util.Fetchable.fetch_marshall(
                QuestionHTMLFetcher(session, 'questions', **{importance: 1}),
                QuestionProcessor(UserQuestion)
            )
            self.importance_name_to_fetchable[importance] = fetchable
            setattr(self, importance, fetchable)
        self._session = session
        if user_id:
            self._user_id = user_id

    @util.cached_property
    def _user_id(self):
        return self._session.get_current_user_profile().id

    def respond_from_user_question(self, user_question, importance):
        """Respond to a question in exactly the way that is described by
        the given user_question.

        :param user_question: The user question to respond with.
        :type user_question: :class:`.UserQuestion`
        :param importance: The importance that should be used in responding to
                           the question.
        :type importance: int see :attr:`.importance_name_to_number`
        """
        user_response_ids = [option.id
                             for option in user_question.answer_options
                             if option.is_users]
        match_response_ids = [option.id
                              for option in user_question.answer_options
                              if option.is_match]
        if len(match_response_ids) == len(user_question.answer_options):
            match_response_ids = 'irrelevant'
        return self.respond(user_question.id, user_response_ids,
                            match_response_ids, importance,
                            note=user_question.explanation or '')

    def respond_from_question(self, question, user_question, importance):
        """Copy the answer given in `question` to the logged in user's
        profile.

        :param question: A :class:`~.Question` instance to copy.
        :param user_question: An instance of :class:`~.UserQuestion` that
                              corresponds to the same question as `question`.
                              This is needed to retrieve the answer id from
                              the question text answer on question.
        :param importance: The importance to assign to the response to the
                           answered question.
        """
        option_index = user_question.answer_text_to_option[
            question.their_answer
        ].id
        self.respond(question.id, [option_index], [option_index], importance)

    def respond(self, question_id, user_response_ids, match_response_ids,
                importance, note='', is_public=1, is_new=1):
        """Respond to an okcupid.com question.

        :param question_id: The okcupid id used to identify this question.
        :param user_response_ids: The answer id(s) to provide to this question.
        :param match_response_ids: The answer id(s) that the user considers
                                   acceptable.
        :param importance: The importance to attribute to this question. See
                           :attr:`.importance_name_to_number` for details.
        :param note: The explanation note to add to this question.
        :param is_public: Whether or not the question answer should be made
                          public.
        """
        form_data = {
            'ajax': 1,
            'submit': 1,
            'answer_question': 1,
            'skip': 0,
            'show_all': 0,
            'targetid': self._user_id,
            'qid': question_id,
            'answers': user_response_ids,
            'matchanswers': match_response_ids,
            'is_new': is_new,
            'is_public': is_public,
            'note': note,
            'importance': importance,
            'delete_note': 0
        }
        return self._session.okc_post(
            self.path, data=form_data, headers=self.headers
        )

    def clear(self):
        """USE WITH CAUTION. Delete the answer to every question that the
        logged in user has responded to.
        """
        return self._session.okc_post(
            'questions', data={'clear_all': 1}, headers=self.headers
        )


_page_data_xpb = xpb.div.with_class('pages_data')
_current_page_xpb = _page_data_xpb.input(id='questions_pages_page').\
                    select_attribute_('value')
_total_page_xpb = _page_data_xpb.input(id='questions_pages_total').\
                  select_attribute_('value')
_question_xpb = xpb.div.with_class('question')


def QuestionProcessor(question_class):
    return util.PaginationProcessor(question_class, _question_xpb,
                                    _current_page_xpb, _total_page_xpb)


class QuestionHTMLFetcher(object):

    @classmethod
    def from_username(cls, session, username, **kwargs):
        return cls(session, u'profile/{0}/questions'.format(username), **kwargs)

    def __init__(self, session, uri, **additional_parameters):
        self._session = session
        self._uri = uri
        self._additional_parameters = additional_parameters

    def _query_params(self, start_at):
        parameters = {'low': start_at, 'leanmode': 1}
        parameters.update(self._additional_parameters)
        return parameters

    def fetch(self, start_at):
        response = self._session.okc_get(self._uri,
                                         params=self._query_params(start_at))
        return response.content.decode('utf8', 'replace')


def QuestionFetcher(session, username, question_class=Question,
                    is_user=False, **kwargs):
    if is_user:
        question_class = UserQuestion
    return util.FetchMarshall(
        QuestionHTMLFetcher.from_username(session, username, **kwargs),
        QuestionProcessor(question_class)
    )
