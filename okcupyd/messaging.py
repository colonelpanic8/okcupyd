import logging

from lxml import html
from requests import exceptions
import simplejson

from . import errors
from . import helpers
from . import util
from .xpath import XPathBuilder, xpb


log = logging.getLogger(__name__)
thread_element_xpath = XPathBuilder(relative=False).li.with_classes('thread',
                                                                    'message')


def ThreadFetcher(session, mailbox_number):
    return util.FetchMarshall(
        ThreadHTMLFetcher(session, mailbox_number),
        util.SimpleProcessor(
            session, lambda elem: MessageThread(session, elem),
            thread_element_xpath
        )
    )


class ThreadHTMLFetcher(object):

    def __init__(self, session, mailbox_number):
        self._session = session
        self._mailbox_number = mailbox_number

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

    def __repr__(self):
        return '{0}(mailbox_number={1})'.format(type(self).__name__,
                                                self._mailbox_number)


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
        messages_response = self._session.okc_get('messages',
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

    _message_elements_xpb = xpb.li.with_classes('to_me', 'from_me').or_

    @util.cached_property
    def message_elements(self):
        return self._message_elements_xpb.apply_(self.messages_tree)


_base_timestamp_xpb = (
    xpb.span.with_class('timestamp').span.with_class('fancydate')
)
_timestamp_xpb = _base_timestamp_xpb.text_
_em_timestamp_xpb = _base_timestamp_xpb.em.text_


class Message(object):
    """Represent a message sent on okcupid.com"""

    def __init__(self, message_element, message_thread):
        self._message_element = message_element
        self._message_thread = message_thread

    @property
    def id(self):
        """
        :returns: The id assigned to this message by okcupid.com.
        """
        return int(self._message_element.attrib['id'].split('_')[-1])

    @util.cached_property
    def sender(self):
        """
        :returns: A :class:`~okcupyd.profile.Profile` instance belonging
                  to the sender of this message.
        """
        return (self._message_thread.user_profile
                if 'from_me' in self._message_element.attrib['class']
                else self._message_thread.correspondent_profile)

    @util.cached_property
    def recipient(self):
        """
        :returns: A :class:`~okcupyd.profile.Profile` instance belonging
                  to the recipient of this message.
        """
        return (self._message_thread.correspondent_profile
                if 'from_me' in self._message_element.attrib['class']
                else self._message_thread.user_profile)

    _content_xpb = xpb.div.with_class('message_body')

    @util.cached_property
    def content(self):
        """
        :returns: The text body of the message.
        """
        # The code that follows is obviously pretty disgusting.
        # It seems like it might be impossible to completely replicate
        # the text of the original message if it has trailing whitespace
        message = self._content_xpb.one_(self._message_element)
        first_line = message.text
        if message.text[:2] == '  ':
            first_line = message.text[2:]
        else:
            log.debug("message did not have expected leading whitespace")
        subsequent_lines = ''.join([
            html.tostring(child, encoding='unicode').replace('<br>', '\n')
            for child in message.iterchildren()
        ])
        message_text = first_line + subsequent_lines
        if len(message_text) > 0 and message_text[-1] == ' ':
            message_text = message_text[:-1]
        else:
            log.debug("message did not have expected leading whitespace")

        return message_text

    @util.cached_property
    def time_sent(self):
        try:
            timestamp_text = _timestamp_xpb.one_(self._message_element)
        except IndexError:
            timestamp_text = _em_timestamp_xpb.one_(self._message_element)
        return helpers.parse_date_updated(timestamp_text)

    def __repr__(self):
        return '<{0}: {1} sent {2} "{3}{4}">'.format(
            type(self).__name__,
            self.sender.username,
            self.recipient.username,
            self.content[:10],
            '...' if len(self.content) > 10 else ''
        )


class MessageThread(object):
    """Represent a message thread between two users."""

    @classmethod
    def delete_threads(cls, session, thread_ids_or_threads, authcode=None):
        """
        :param session: A logged in :class:`~okcupyd.session.Session`.
        :param thread_ids_or_threads: A list whose members are either
                                      :class:`~.MessageThread` instances
                                      or okc_ids of message threads.
        :param authcode: Authcode to use for this request. If none is provided
                         A request to the logged in user's messages page
                         will be made to retrieve one.
        """
        thread_ids = [thread.id if isinstance(thread, cls) else thread
                      for thread in thread_ids_or_threads]
        if not authcode:
            authcode = helpers.get_authcode(html.fromstring(
                session.okc_get('messages').content
            ))
        data = {'access_token': authcode,
                'threadids': simplejson.dumps(thread_ids)}
        return session.okc_delete('apitun/messages/threads',
                                  params=data, data=data)

    def __init__(self, session, thread_element):
        self._session = session
        self._thread_element = thread_element
        self.reply = self.correspondent_profile.message(thread_id=self.id)
        self._message_fetcher = MessageFetcher(self._session, self)
        #: A :class:`~okcupyd.util.fetchable.Fetchable` of :class:`~.Message`
        #: objects.
        self.messages = util.Fetchable(self._message_fetcher)

    @util.cached_property
    def id(self):
        """
        :returns: The id assigned to this message by okcupid.com.
        """
        return self._thread_element.attrib['data-threadid']

    @util.cached_property
    def correspondent_id(self):
        """
        :returns: The id assigned to the correspondent of this message.
        """
        try:
            return int(self._thread_element.attrib['data-personid'])
        except (ValueError, KeyError):
            try:
                return int(self.correspondent_profile.id)
            except:
                pass

    _correspondent_xpb = xpb.div.with_class('inner').a.with_class('open').\
                         span.with_class('subject').text_

    @util.cached_property
    def correspondent(self):
        """
        :returns: The username of the user with whom the logged in user is
                  conversing in this :class:`~.MessageThread`.
        """
        try:
            return self._correspondent_xpb.one_(self._thread_element).strip()
        except IndexError:
            raise errors.NoCorrespondentError()

    @util.cached_property
    def read(self):
        """
        :returns: Whether or not the user has read all the messages in this
                  :class:`~.MessageThread`.
        """
        return not 'unreadMessage' in self._thread_element.attrib['class']

    @util.cached_property
    def date(self):
        return self.datetime.date()

    @util.cached_property
    def datetime(self):
        return helpers.parse_date_updated(
            _timestamp_xpb.one_(self._thread_element)
        )

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
        """
        :returns: A :class:`~okcupyd.profile.Profile` instance belonging to the
                  initiator of this :class:`~.MessageThread`.
        """
        try:
            return self.messages[0].sender
        except IndexError:
            pass

    @property
    def respondent(self):
        """
        :returns: A :class:`~okcupyd.profile.Profile` instance belonging to the
                  respondent of this :class:`~.MessageThread`.
        """
        try:
            return self.messages[0].recipient
        except IndexError:
            pass

    @util.cached_property
    def correspondent_profile(self):
        """
        :returns: The :class:`~okcupyd.profile.Profile` of the user with whom
                  the logged in user is conversing in this
                  :class:`~.MessageThread`.
        """
        return self._session.get_profile(self.correspondent)

    @util.cached_property
    def user_profile(self):
        """
        :returns: A :class:`~okcupyd.profile.Profile` belonging to the logged
                  in user.
        """
        return self._session.get_current_user_profile()

    @property
    def message_count(self):
        return len(self.messages)

    @property
    def has_messages(self):
        return bool(self.messages)

    @property
    def got_response(self):
        """
        :returns: Whether or not the :class:`~.MessageThread`. has received a
                  response.
        """
        return any(message.sender != self.initiator
                   for message in self.messages)

    def delete(self):
        """Delete this thread for the logged in user."""
        return self.delete_threads(self._session, [self.id])

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return '<{0}({1}, {2})>'.format(
            type(self).__name__,
            self.user_profile.username,
            self.correspondent_profile.username
        )
