from lxml import html

from . import helpers
from . import util


class Profile(object):

    def __init__(self, session, username, *args, **kwargs):
        self.username = username
        self._session = session
        for key, value in kwargs.items():
            setattr(self, key, value)

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

    def __repr__(self):
        return 'Profile("{0}")'.format(self.username)
