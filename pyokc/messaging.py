from collections import namedtuple
import itertools
import logging

from lxml import html

from . import helpers
from . import util
from .xpath import XPathBuilder


log = logging.getLogger()


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

        correspondent = XPathBuilder().div.with_class('inner').a.with_class('photo').img.apply_(message_element)[0].attrib['alt'].split()[-1]

        read = not 'unreadMessage' in message_element.attrib['class']

        timestamp_span = XPathBuilder().span.with_class('timestamp').apply_(message_element)
        date_updated_text = timestamp_span[0][0].text
        date_updated = helpers.parse_date_updated(date_updated_text)

        return MessageThread(thread_id, correspondent, read, date_updated,
                             session=self._session)

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
