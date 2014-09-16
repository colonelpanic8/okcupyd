from lxml import html

from . import helpers
from . import util


class Question(object):

    def __init__(self, text, user_answer, explanation):
        self.text = text
        self.user_answer = user_answer
        self.explanation = explanation

    def __repr__(self):
        return '<Question: {0}>'.format(self.text)


class Profile(object):

    def __init__(self, session, username, *args, **kwargs):
        self.username = username
        self._session = session
        for key, value in kwargs.items():
            setattr(self, key, value)

        self._initialize_fillable_traits()

    @util.cached_property
    def _profile_response(self):
        return self._session.get(
            'https://www.okcupid.com/profile/{0}'.format(self.username)
        ).content.decode('utf8')

    @util.cached_property
    def authcode(self):
        return helpers.get_authcode(self._profile_response)

    @util.cached_property
    def _profile_tree(self):
        return html(self._profile_response)

    def message_request_parameters(self, content, thread_id):
        return {
            'ajax': 1,
            'sendmsg': 1,
            'r1': self.username,
            'body': content,
            'threadid': thread_id,
            'authcode': self.authcode,
            'reply': 1 if thread_id else 0,
            'from_profile': 1
        }

    @util.n_partialable
    def message(self, message, thread_id=None):
        return helpers.MessageSender(self._session).send_message(self.username, message, self.authcode, thread_id)


    def _initialize_fillable_traits(self):
        self.pics = []
        self.questions = []
        self.traits = []
        self.essays = {
            'self summary': '',
            'life': '',
            'good at': '',
            'first things': '',
            'favorites': '',
            'six things': '',
            'thinking': '',
            'friday night': '',
            'private thing': '',
            'message me if': '',
            }
        self.looking_for = {
            'gentation': '',
            'ages': '',
            'near': '',
            'single': '',
            'seeking': '',
            }
        self.details = {
            'last online': '',
            'orientation': '',
            'ethnicity': '',
            'height': '',
            'body type': '',
            'diet': '',
            'smokes': '',
            'drinks': '',
            'drugs': '',
            'religion': '',
            'sign': '',
            'education': '',
            'job': '',
            'income': '',
            'relationship type': '',
            'offspring': '',
            'pets': '',
            'speaks': '',
            }

    def update_questions(self):
        """
        Update self.questions with Question instances, which contain
        text, user_answer, and explanation attributes. See
        the Question class in objects.py for more details. Like
        User.update_questions(), note that this can take a while due to
        OKCupid displaying only ten questions on each page, potentially
        requiring a large number of requests to the server.
        """
        keep_going = True
        question_number = 0
        while keep_going:
            questions_data = {
                'low': 1 + question_number,
                }
            get_questions = self._session.post(
            'http://www.okcupid.com/profile/{0}/questions'.format(self.name),
            data=questions_data)
            tree = html.fromstring(get_questions.content.decode('utf8'))
            next_wrapper = tree.xpath("//li[@class = 'next']")
            question_wrappers = tree.xpath("//div[contains(@id, 'question_')]")
            for div in question_wrappers:
                if not div.attrib['id'][9:].isdigit():
                    question_wrappers.remove(div)
            for div in question_wrappers:
                question_number += 1
                explanation = ''
                text = helpers.replace_chars(div.xpath(".//div[@class = 'qtext']/p/text()")[0])
                user_answer = div.xpath(".//span[contains(@id, 'answer_target_')]/text()")[0].strip()
                explanation_span = div.xpath(".//span[@class = 'note']")
                if explanation_span[0].text is not None:
                    explanation = explanation_span[0].text.strip()
                self.questions.append(Question(text, user_answer, explanation))
            if not len(next_wrapper):
                keep_going = False

    def update_traits(self):
        """
        Fill `self.traits` the personality traits of this profile.
        """
        get_traits = self._session.get('http://www.okcupid.com/profile/{0}/personality'.format(self.name))
        tree = html.fromstring(get_traits.content.decode('utf8'))
        self.traits = tree.xpath("//div[@class = 'pt_row']//label/text()")

    def update_pics(self):
        """
        Fill `self.pics` with url strings of pictures for this profile.
        """
        pics_request = self._session.get('http://www.okcupid.com/profile/{0}/photos?cf=profile'.format(self.name))
        pics_tree = html.fromstring(pics_request.content.decode('utf8'))
        self.pics = pics_tree.xpath("//div[@id = 'album_0']//img/@src")

    def __repr__(self):
        return 'Profile("{0}")'.format(self.username)

