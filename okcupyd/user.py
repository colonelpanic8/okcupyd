from lxml import html

from . import helpers
from . import util
from .attractiveness_finder import AttractivenessFinder
from .messaging import ThreadFetcher
from .photo import PhotoUploader
from .profile import Profile
from .question import Questions
from .search import SearchManager
from .session import Session
from .xpath import xpb


class User(object):
    """Encapsulate a logged in okcupid user."""

    @classmethod
    def with_credentials(cls, username, password):
        """
        :param username: The username to log in with.
        :type username: str
        :param password: The password to log in with.
        :type password: str
        """
        return cls(Session.login(username, password))

    def __init__(self, session=None):
        """
        :param session: A logged in :class:`okcupyd.session.Session`
        """
        self._session = session or Session.login()
        self._message_sender = helpers.Messager(self._session)
        assert self._session.log_in_name is not None, (
            "The session provided to the user constructor must be logged in."
        )
        #: A :class:`okcupyd.profile.Profile` belonging to the logged in user.
        self.profile = Profile(self._session, self._session.log_in_name)

        #: A :class:`okcupyd.util.Fetchable` of
        #: :class:`okcupyd.messaging.MessageThread` objects corresponding to
        #: messages that are currently in the user's inbox.
        self.inbox = util.Fetchable(ThreadFetcher(self._session, 1))
        #: A :class:`okcupyd.util.Fetchable` of
        #: :class:`okcupyd.messaging.MessageThread` objects corresponding to
        #: messages that are currently in the user's outbox.
        self.outbox = util.Fetchable(ThreadFetcher(self._session, 2))
        #: A :class:`okcupyd.util.Fetchable` of
        #: :class:`okcupyd.messaging.MessageThread` objects corresponding to
        #: messages that are currently in the user's drafts folder.
        self.drafts = util.Fetchable(ThreadFetcher(self._session, 4))
        #: A :class:`okcupyd.util.Fetchable` of
        #: :class:`okcupyd.profile.Profile` objects of okcupid.com users that have
        #: visited this user's profile.
        # self.visitors = util.Fetchable()

        #: A :class:`okcupyd.question.Questions` that is instantiated with
        #: this instance's session.
        self.questions = Questions(self._session)
        self.attractiveness_finder = AttractivenessFinder(self._session)
        self.photo = PhotoUploader(self._session)

    def get_profile(self, username):
        """Get the :class:`okcupyd.profile.Profile` associated with the supplied
        username.
        :param username: The username of the profile to retrieve.
        """
        return self._session.get_profile(username)

    _visitors_xpb = xpb.div.with_class('user_info').\
                   div.with_class('profile_info').div.with_class('username').\
                   a.with_class('name')

    _visitors_xpb = xpb.div.with_class('username').\
                   a.with_class('name')

    @property
    def username(self):
        return self.profile.username

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
        """Return a :class:`okcupyd.search.SearchManager` built with this
        object's session object.
        Defaults for `gender`, `looking_for`, `location` and `radius` will
        be provided to the constructor of the
        :class:`okcupyd.search.SearchManager` unless they are explicitly
        provided.
        :param kwargs: Arguments that should be passed to the constructor of the
        :class:`okcupyd.search.SearchManager`
        """
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

    def __repr__(self):
        return 'User("{0}")'.format(self.profile.username)
