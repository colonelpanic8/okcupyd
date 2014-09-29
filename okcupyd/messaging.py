from collections import namedtuple
import logging

from lxml import html

from . import helpers
from . import util
from .xpath import XPathBuilder, xpb


log = logging.getLogger(__name__)


def ThreadFetcher(session, mailbox_number):
    return util.StepObjectFetcher(ThreadHTMLFetcher(session, mailbox_number),
                                  ThreadProcessor(session))


class ThreadHTMLFetcher(object):

    def __init__(self, session, mailbox_number, step=30):
        self._session = session
        self._mailbox_number = mailbox_number
        self.step = step

    def _query_params(self, start_at):
        return {
            'low': start_at,
            'folder': self._mailbox_number,
            'infiniscroll': 1
        }

    def fetch(self, start_at):
        response = self._session.okc_get('messages',
                                         params=self._query_params(start_at))
        return response.content.strip()


class ThreadProcessor(object):

    xpath_builder = XPathBuilder(relative=False).li.with_classes('thread', 'message')

    def __init__(self, session, id_to_existing=None):
        self._session = session
        self.id_to_existing = id_to_existing or {}

    def process(self, text_response):
        for thread_element in self.xpath_builder.apply_(html.fromstring(text_response)):
            yield self._process_thread_element(thread_element)

    def _process_thread_element(self, thread_element):
        id = thread_element.attrib['data-threadid']
        if self.id_to_existing is not None and id in self.id_to_existing:
            return self.id_to_existing[id]

        correspondent_id = thread_element.attrib['data-personid']

        correspondent = xpb.div.with_class('inner').a.with_class('photo').\
                        img.select_attribute_('alt', thread_element)[0].split()[-1]

        read = not 'unreadMessage' in thread_element.attrib['class']

        timestamp_span = xpb.span.with_class('timestamp').apply_(thread_element)
        date_updated_text = timestamp_span[0][0].text_content()
        date_updated = helpers.parse_date_updated(date_updated_text)

        return MessageThread(id, correspondent, correspondent_id, read,
                             date_updated, session=self._session)


class MessageRetriever(object):

    def __init__(self, session, id, read_messages=False):
        self._session = session
        self._read_messages = read_messages
        self.id = id

    @property
    def params(self):
        return {
            'readmsg': str(self._read_messages).lower(),
            'threadid': self.id,
            'folder': 1
        }

    def thread_tree(self):
        messages_response = self._session.get('https://www.okcupid.com/messages',
                                              params=self.params)
        return html.fromstring(messages_response.content.decode('utf8'))

    user_xpath = xpb.div.with_class('profile_info').div.\
                 with_class('username').span.with_class('name').xpath

    def get_usernames(self, tree):
        try:
            them = tree.xpath(self.user_xpath)[0].text
        except IndexError:
            title_element = xpb.title.apply_(tree)[0]
            them = title_element.text.split()[-1]

        return helpers.get_my_username(tree), them

    def get_message_elements(self, thread_tree):
        return xpb.li.with_classes('to_me', 'from_me')._or.apply_(thread_tree)

    def get_messages(self):
        tree = self.thread_tree()
        me, them = self.get_usernames(tree)
        for message_element in self.get_message_elements(tree):
            if 'from_me' in message_element.attrib['class']:
                sender, recipient = me, them
            else:
                sender, recipient = them, me
            message_id = message_element.attrib['id'].split('_')[-1]
            message = xpb.div.with_class('message_body').apply_(message_element)
            if message_id == 'compose':
                continue
            content = None
            if message:
                message = message[0]
                content = message.text_content().replace(' \n \n', '\n').strip()

            yield Message(message_id, sender, recipient, content)


Message = namedtuple('Message', ('id', 'sender', 'recipient', 'content'))


class MessageThread(object):

    def __init__(self, id, correspondent, correspondent_id, read,
                 date, session=None):
        self._session = session
        self._message_retriever = MessageRetriever(session, id)
        self.id = id
        self.correspondent = correspondent
        self.correspondent_id = correspondent_id
        self.read = read
        self.date = date
        self.reply = self.correspondent_profile.message(thread_id=self.id)

    @property
    def initiator(self):
        if not self.messages:
            return
        return self.user_profile \
            if self.user_profile.username == self.messages[0].sender \
               else self.correspondent_profile


    @property
    def respondent(self):
        if not self.messages:
            return
        return self.correspondent_profile \
            if self.user_profile.username == self.messages[0].sender \
               else self.correspondent_profile

    @property
    def redact_messages(self):
        return self.restore(self.id, self.correspondent, self.read, self.date,
                            session=self._session,
                            messages=[self.redact_message(message)
                                      for message in self.messages])

    @staticmethod
    def redact_message(message):
        return Message(message.id, message.sender, message.recipient,
                       'x'*len(message.content))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    @util.cached_property
    def messages(self):
        return self.get_messages()

    @util.cached_property
    def correspondent_profile(self):
        return self._session.get_profile(self.correspondent)

    @util.cached_property
    def user_profile(self):
        return self._session.get_current_user_profile()

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
    def has_messages(self):
        return bool(self.messages)

    @property
    def got_response(self):
        return any(message.sender != self.initiator for message in self.messages)

    @property
    def as_dict(self):
        return {
            'id': self.id,
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
            'threadid': self.id,
            'receiverid': self.correspondent_id,
            'folderid': 1,
            'body_to_forward': self.messages[-1].content
        }
