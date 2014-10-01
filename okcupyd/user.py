from lxml import html

from . import helpers
from . import util
from .messaging import ThreadFetcher
from .photo import PhotoUploader
from .profile import Profile
from .question import Questions
from .search import SearchManager
from .session import Session
from .xpath import xpb


class User(object):

    @classmethod
    def with_credentials(cls, username, password):
        return cls(Session.login(username, password))

    def __init__(self, session=None):
        self._session = session or Session.login()
        assert self._session.log_in_name is not None, (
            "The session provided to the user constructor must be logged in."
        )

        self.profile = Profile(self._session, self._session.log_in_name)
        self.authcode = self.profile.authcode

        self._message_sender = helpers.Messager(self._session)
        self.inbox = util.Fetchable(ThreadFetcher(self._session, 1))
        self.outbox = util.Fetchable(ThreadFetcher(self._session, 2))
        self.drafts = util.Fetchable(ThreadFetcher(self._session, 4))
        self.questions = Questions(self._session)

    def get_profile(self, username):
        return self._session.get_profile(username)

    _visitors_xpb = xpb.div.with_class('user_info').\
                   div.with_class('profile_info').div.with_class('username').\
                   a.with_class('name')

    _visitors_xpb = xpb.div.with_class('username').\
                   a.with_class('name')

    @util.cached_property
    def visitors(self):
        visitors_response = self._session.okc_get('visitors').content.decode('utf8')
        visitors_tree = html.fromstring(visitors_response)
        return [Profile(self._session, username)
                for username in self._visitors_xpb.text_.apply_(visitors_tree)]

    def message(self, username, message_text):
        # Try to reply to an existing thread.
        if not isinstance(username, str):
            username = username.username
        for thread in sorted(set(self.inbox + self.outbox),
                             key=lambda t: t.datetime, reverse=True):
            if thread.correspondent.lower() == username.lower():
                thread.reply(message_text)
                return

        return self._message_sender.send(username, message_text)

    def search(self, **kwargs):
        if 'count' in kwargs:
            count = kwargs.pop('count')
            return self.search_manager(**kwargs).get_profiles(count=count)
        return util.Fetchable(self.search_manager(**kwargs))

    def search_manager(self, **kwargs):
        kwargs.setdefault('gender', self.profile.gender[0])
        looking_for = helpers.get_looking_for(self.profile.gender,
                                              self.profile.orientation)
        kwargs.setdefault('looking_for', looking_for)
        kwargs.setdefault('location', self.profile.location)
        kwargs.setdefault('radius', 25)
        return SearchManager(session=self._session, **kwargs)

    def quickmatch(self):
        """Return a Profile obtained by visiting the quickmatch page."""
        response = self._session.okc_get('quickmatch', params={'okc_api': 1})
        return Profile(self._session, response.json()['sn'])

    def upload_photo(self, filename):
        return PhotoUploader(filename, self._session,
                             user_id=self.profile._current_user_id)

    def __repr__(self):
        return 'User("{0}")'.format(self.profile.username)
