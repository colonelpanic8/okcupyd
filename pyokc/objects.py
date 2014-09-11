from collections import namedtuple
from time import clock
import itertools

from lxml import html
import requests

from . import helpers
from . import util
from .settings import DELAY, USERNAME, PASSWORD
from .xpath import XPathBuilder


class Session(requests.Session):

    @classmethod
    def login(cls, username=USERNAME, password=PASSWORD, headers=None):
        session = cls()
        helpers.login(session, {'username': username, 'password': password}, headers)
        return session

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp = -DELAY

    def post(self, *args, **kwargs):
        while clock() - self.timestamp < DELAY:
            pass
        self.timestamp = clock()
        response = super().post(*args, **kwargs)
        response.raise_for_status()
        return response

    def get(self, *args, **kwargs):
        while clock() - self.timestamp < DELAY:
            pass
        self.timestamp = clock()
        response = super().get(*args, **kwargs)
        response.raise_for_status()
        return response


class MailboxFetcher(object):

    step = 30

    def __init__(self, session, mailbox_number):
        self._session = session
        self.mailbox_number = mailbox_number

    def _form_data(self, start_at):
        return {
            'low': start_at,
            'folder': self.mailbox_number,
            'infiniscroll': 1
        }

    def process_message_element(self, message_element):
        thread_id = message_element.attrib['data-threadid']

        correspondent = XPathBuilder().span.with_class('subject').get_text_(message_element)

        read = not 'unreadMessage' in message_element.attrib['class']

        timestamp_span = XPathBuilder().span.with_class('timestamp').apply_(message_element)
        date_updated_text = timestamp_span[0][0].text
        date_updated = helpers.parse_date_updated(date_updated_text)

        return MessageThread(thread_id, correspondent, read, date_updated, session=self._session)

    def get_threads(self, start_at=0, get_at_least=None):
        start_at_iterator = (range(start_at + 1, get_at_least + 1, self.step)
                                if get_at_least
                                else itertools.count(start_at + 1, self.step))
        for start_at in start_at_iterator:
            messages_response = self._session.get('https://www.okcupid.com/messages',
                                                   params=self._form_data(start_at))
            messages_text = messages_response.content.decode('utf8').strip()
            if not messages_text: break
            inbox_tree = html.fromstring(messages_text)
            message_elements = util.find_elements_with_classes(inbox_tree, 'li',
                                                               ['thread', 'message'])
            for message_element in message_elements:
                yield self.process_message_element(message_element)


class MessageRetriever(object):

    def __init__(self, session, thread_id):
        self._session = session
        self.thread_id = thread_id

    @property
    def params(self):
        return {
            'readmsg': 'true',
            'threadid': self.thread_id,
            'folder': 1
        }

    def thread_tree(self):
        messages_response = self._session.get('https://www.okcupid.com/messages',
                                              params=self.params)
        return html.fromstring(messages_response.content.decode('utf8'))

    def get_usernames(self, tree):
        xpath_string = XPathBuilder().div.with_class('profile_info').div.with_class('username').span.with_class('name').xpath
        try:
            them = tree.xpath(xpath_string)[0].text
        except IndexError:
            title_element = XPathBuilder().title.apply_(tree)[0]
            them = title_element.text.split()[-1]

        return helpers.get_my_username(tree), them

    def get_message_elements(self, thread_tree):
        return util.find_elements_with_classes(thread_tree, 'li',
                                               ['to_me', 'from_me'], is_or=True)

    def get_messages(self):
        tree = self.thread_tree()
        me, them = self.get_usernames(tree)
        for message_element in self.get_message_elements(tree):
            if 'from_me' in message_element.attrib['class']:
                sender, recipient = me, them
            else:
                sender, recipient = them, me
            message_id = message_element.attrib['id'].split('_')[-1]
            message = util.find_elements_with_classes(message_element,
                                                  'div', ['message_body'])
            if message_id == 'compose':
                continue
            content = None
            if message:
                message = message[0]
                content = message.text_content().replace(' \n \n', '\n').strip()

            yield Message(message_id, sender, recipient, content)


Message = namedtuple('Message', ('id', 'sender', 'recipient', 'content'))


class MessageThread(object):

    @classmethod
    def restore(cls, thread_id, correspondent, read, date, session=None,
                messages=None):

        instance = cls(thread_id, correspondent, read, date, session)
        if messages is not None:
            instance.__dict__['messages'] = messages
        return instance

    def __init__(self, thread_id, correspondent, read, date, session=None):
        self._session = session
        self._message_retriever = MessageRetriever(session, thread_id)
        self.correspondent = correspondent
        self.thread_id = thread_id
        self.read = read
        self.date = date

    def __hash__(self):
        return hash(self.thread_id)

    def __eq__(self, other):
        return self.thread_id == other.thread_id

    @util.cached_property
    def messages(self):
        return self.get_messages()

    def get_messages(self):
        return list(self._message_retriever.get_messages())

    @property
    def refreshed_messages(self):
        if 'messages' in self.__dict__['messages']: del self.__dict__['messages']
        return self.messages

    @property
    def message_count(self):
        return len(self.messages)

    @property
    def initiator(self):
        if self.messages:
            return self.messages[0].sender

    @property
    def has_messages(self):
        return bool(self.messages)

    @property
    def got_response(self):
        return any(message.sender != self.initiator for message in self.messages)

    @property
    def as_dict(self):
        return {
            'thread_id': self.thread_id,
            'correspondent': self.correspondent,
            'read': self.read,
            'date': self.date.strftime('%Y-%m-%d'),
            'messages': list(map(self.message_as_dict, self.messages))
        }

    @staticmethod
    def message_as_dict(message):
        return {
            'id': message.id,
            'sender': message.sender,
            'recipient': message.recipient,
            'content': message.content
        }


class Question(object):

    def __init__(self, text, user_answer, explanation):
        self.text = text
        self.user_answer = user_answer
        self.explanation = explanation

    def __repr__(self):
        return '<Question: {0}>'.format(self.text)


class Profile(object):
    """
    Represent another user on OKCupid. You should not initialize these
    on their own. Instead, User.search() returns a list of Profile
    objects, and User.visit() returns a single Profile object. You can
    also find a list of Profile objects in User.visitors. Most of the
    attributes will be empty until User.visit() is called.
    self.questions, self.traits, and self.pics will remain empty until
    self.update_questions(), self.update_traits(), and
    self.update_pics() are called, respectively.
    Parameters
    ----------
    name : str
        The username of this profile.
    age : int
        The age of this profile's user.
    location : str
        The geographical location of this profile's user.
    match : int
        The match percentage that you have with this profile.
    enemy : int
        The enemy percentage that you have with this profile.
    rating : int
        The rating you gave this profile.
    contacted : bool
        Whether you've contacted this user or not.
    """
    def __init__(self, _session, name, age=None, location='', match=None,
                 enemy=None, id=None, rating=0, contacted=False):
        self._session = _session
        self._id = id
        self.name = name
        self.age = age
        self.location = location
        self.match = match
        self.enemy = enemy
        self.rating = rating
        self.contacted = contacted
        self.gender = None
        self.orientation = None
        self.status = None
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
        return '<Profile of {0}>'.format(self.name)
