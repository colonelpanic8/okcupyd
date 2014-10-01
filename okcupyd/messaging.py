import logging

from lxml import html
from requests import exceptions

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

        return MessageThread(self._session, thread_element)


class MessageFetcher(object):

    def __init__(self, session, message_thread, read_messages=False):
        self._session = session
        self._read_messages = read_messages
        self._message_thread = message_thread

    @property
    def params(self):
        return {
            'readmsg': str(self._read_messages).lower(),
            'threadid': self._message_thread.id,
            'folder': 1
        }

    @util.cached_property
    def messages_tree(self):
        messages_response = self._session.get('https://www.okcupid.com/messages',
                                              params=self.params)
        return html.fromstring(messages_response.content.decode('utf8'))

    def refresh(self):
        util.cached_property.bust_caches(self)
        return self.messages_tree

    def fetch(self):
        for message_element in self.message_elements:
            if message_element.attrib['id'] == 'compose':
                continue
            yield Message(message_element, self._message_thread)

    @util.cached_property
    def message_elements(self):
        return xpb.li.with_classes('to_me', 'from_me')._or.apply_(self.messages_tree)


class Message(object):

    def __init__(self, message_element, message_thread):
        self._message_element = message_element
        self._message_thread = message_thread

    @property
    def id(self):
        return int(self._message_element.attrib['id'].split('_')[-1])

    @util.cached_property
    def sender(self):
        return (self._message_thread.user_profile
                if 'from_me' in self._message_element.attrib['class']
                else self._message_thread.correspondent_profile)

    @util.cached_property
    def recipient(self):
        return (self._message_thread.correspondent_profile
                if 'from_me' in self._message_element.attrib['class']
                else self._message_thread.user_profile)

    @util.cached_property
    def content(self):
        message = xpb.div.with_class('message_body').apply_(self._message_element)
        content = None
        if message:
            message = message[0]
            content = message.text_content().replace(' \n \n', '\n').strip()
        return content


class MessageThread(object):

    def __init__(self, session, thread_element):
        self._session = session
        self._thread_element = thread_element
        self.reply = self.correspondent_profile.message(thread_id=self.id)
        self._message_fetcher = MessageFetcher(self._session, self)
        self.messages = util.Fetchable(self._message_fetcher)

    @util.cached_property
    def id(self):
        return self._thread_element.attrib['data-threadid']

    @util.cached_property
    def correspondent_id(self):
        return self._thread_element['data-personid']

    _correspondent_xpb = xpb.div.with_class('inner').a.with_class('photo').\
                             img.select_attribute_('alt')

    @util.cached_property
    def correspondent(self):
        return self._correspondent_xpb.apply_(self._thread_element)[0].split()[-1]

    @util.cached_property
    def read(self):
        return not 'unreadMessage' in self._thread_element.attrib['class']

    @util.cached_property
    def date(self):
        return self.datetime.date()

    @util.cached_property
    def datetime(self):
        timestamp_span = xpb.span.with_class('timestamp').apply_(self._thread_element)
        date_updated_text = timestamp_span[0][0].text_content()
        return helpers.parse_date_updated(date_updated_text)

    @property
    def with_deleted_user(self):
        try:
            self.correspondent_profile.id
        except exceptions.HTTPError:
            return True
        else:
            return False

    @property
    def initiator(self):
        try:
            return self.messages[0].sender
        except IndexError:
            pass

    @property
    def respondent(self):
        try:
            return self.messages[0].recipient
        except IndexError:
            pass

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

    @util.cached_property
    def correspondent_profile(self):
        return self._session.get_profile(self.correspondent)

    @util.cached_property
    def user_profile(self):
        return self._session.get_current_user_profile()

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

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id
