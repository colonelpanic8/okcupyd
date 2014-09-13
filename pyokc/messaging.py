from collections import namedtuple
import itertools
import logging

from lxml import html

from . import helpers
from . import util
from .profile import Profile
from .xpath import XPathBuilder


log = logging.getLogger()


class Mailbox(object):

    def __init__(self, session, mailbox_number):
        self._mailbox_fetcher = MailboxFetcher(session, mailbox_number)

    @util.cached_property
    def threads(self):
        return list(self._mailbox_fetcher.get_threads())

    def refresh(self, use_existing=True):
        if 'threads' in self.__dict__:
            self.threads = list(self._mailbox_fetcher.get_threads(
                existing=self.threads if use_existing else ()
            ))
        return self.threads

    def __iter__(self):
        return iter(self.threads)

    def __getitem__(self, item):
        return self.threads[item]


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

    def process_message_element(self, message_element, id_to_existing_thread):
        thread_id = message_element.attrib['data-threadid']
        if thread_id in id_to_existing_thread:
            return id_to_existing_thread[thread_id]

        correspondent_id = message_element.attrib['data-personid']

        correspondent = XPathBuilder().div.with_class('inner').a.with_class('photo').img.apply_(message_element)[0].attrib['alt'].split()[-1]

        read = not 'unreadMessage' in message_element.attrib['class']

        timestamp_span = XPathBuilder().span.with_class('timestamp').apply_(message_element)
        date_updated_text = timestamp_span[0][0].text_content()
        date_updated = helpers.parse_date_updated(date_updated_text)

        return MessageThread(thread_id, correspondent, correspondent_id, read,
                             date_updated, session=self._session)

    def get_threads(self, start_at=0, get_at_least=None, existing=()):
        id_to_existing_thread = {thread.thread_id: thread for thread in existing}
        start_at_iterator = (range(start_at + 1, get_at_least + 1, self.step)
                                if get_at_least
                                else itertools.count(start_at + 1, self.step))
        for start_at in start_at_iterator:
            messages_response = self._session.get('https://www.okcupid.com/messages',
                                                   params=self._form_data(start_at))
            messages_text = messages_response.content.decode('utf8').strip()
            if not messages_text: break
            inbox_tree = html.fromstring(messages_text)
            message_elements = XPathBuilder(relative=False).li.with_classes('thread', 'message').apply_(inbox_tree)
            for message_element in message_elements:
                yield self.process_message_element(message_element,
                                                   id_to_existing_thread)


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
        return XPathBuilder().li.with_classes('to_me', 'from_me')._or.apply_(thread_tree)

    def get_messages(self):
        tree = self.thread_tree()
        me, them = self.get_usernames(tree)
        for message_element in self.get_message_elements(tree):
            if 'from_me' in message_element.attrib['class']:
                sender, recipient = me, them
            else:
                sender, recipient = them, me
            message_id = message_element.attrib['id'].split('_')[-1]
            message = XPathBuilder().div.with_class('message_body').apply_(message_element)
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
    def restore(cls, thread_id, correspondent, correspondent_id, read, date,
                session=None, messages=None):

        instance = cls(thread_id, correspondent, correspondent_id, read, date,
                       session)
        if messages is not None:
            instance.__dict__['messages'] = messages
        return instance

    def __init__(self, thread_id, correspondent, correspondent_id, read,
                 date, session=None):
        self._session = session
        self._message_retriever = MessageRetriever(session, thread_id)
        self.correspondent = correspondent
        self.correspondent_id = correspondent_id
        self.thread_id = thread_id
        self.read = read
        self.date = date
        self.reply = self.correspondent_profile.message(thread_id=self.thread_id)

    @property
    def redact_messages(self):
        return self.restore(self.thread_id, self.correspondent, self.read, self.date,
                            session=self._session,
                            messages=[self.redact_message(message)
                                      for message in self.messages])

    @staticmethod
    def redact_message(message):
        return Message(message.id, message.sender, message.recipient,
                       'x'*len(message.content))

    def __hash__(self):
        return hash(self.thread_id)

    def __eq__(self, other):
        return self.thread_id == other.thread_id

    @util.cached_property
    def messages(self):
        return self.get_messages()

    @util.cached_property
    def correspondent_profile(self):
        return Profile(self._session, self.correspondent)

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
            'correspondent_id': self.correspondent_id,
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

    def delete(self):
        return self._session.post('https://www.okcupid.com/mailbox',
                                  params=self.delete_params)

    @property
    def delete_params(self):
        return {
            'deletethread': 'DELETE',
            'mailaction': 3,
            'buddyname': self.correspondent,
            'r1': self.correspondent,
            'threadid': self.thread_id,
            'receiverid': self.correspondent_id,
            'folderid': 1,
            'body_to_forward': self.messages[-1].content
        }
