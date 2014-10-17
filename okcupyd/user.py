import six

from . import helpers
from . import util
from .attractiveness_finder import AttractivenessFinder
from .messaging import ThreadFetcher
from .photo import PhotoUploader
from .profile import Profile
from .profile_copy import Copy
from .question import Questions
from .search import SearchFetchable, search
from .session import Session
from .xpath import xpb


class User(object):
    """Encapsulate a logged in okcupid user."""

    @classmethod
    def from_credentials(cls, username, password):
        """
        :param username: The username to log in with.
        :type username: str
        :param password: The password to log in with.
        :type password: str
        """
        return cls(Session.login(username, password))

    _visitors_xpb = xpb.div.with_class('user_info').\
                   div.with_class('profile_info').div.with_class('username').\
                   a.with_class('name').text_

    _visitors_current_page_xpb = xpb.div.with_class('pages').\
                                 span.with_class('curpage').text_
    _visitors_total_page_xpb = xpb.div.with_class('pages').\
                               a.with_class('last').text_

    def __init__(self, session=None):
        """
        :param session: A logged in :class:`~okcupyd.session.Session`
        """
        self._session = session or Session.login()
        self._message_sender = helpers.Messager(self._session)
        assert self._session.log_in_name is not None, (
            "The session provided to the user constructor must be logged in."
        )
        #: A :class:`~okcupyd.profile.Profile` object belonging to the logged
        #: in user.
        self.profile = Profile(self._session, self._session.log_in_name)

        #: A :class:`~okcupyd.util.fetchable.Fetchable` of
        #: :class:`~okcupyd.messaging.MessageThread` objects corresponding to
        #: messages that are currently in the user's inbox.
        self.inbox = util.Fetchable(ThreadFetcher(self._session, 1))
        #: A :class:`~okcupyd.util.fetchable.Fetchable` of
        #: :class:`~okcupyd.messaging.MessageThread` objects corresponding to
        #: messages that are currently in the user's outbox.
        self.outbox = util.Fetchable(ThreadFetcher(self._session, 2))
        #: A :class:`~okcupyd.util.fetchable.Fetchable` of
        #: :class:`~okcupyd.messaging.MessageThread` objects corresponding to
        #: messages that are currently in the user's drafts folder.
        self.drafts = util.Fetchable(ThreadFetcher(self._session, 4))

        #: A :class:`~okcupyd.util.fetchable.Fetchable` of
        #: :class:`~okcupyd.profile.Profile` objects of okcupid.com users that
        #: have visited the user's profile.
        self.visitors = util.Fetchable.fetch_marshall(
            util.GETFetcher(self._session, 'visitors',
                            lambda start_at: {'low': start_at}),
            util.PaginationProcessor(
                lambda user: Profile(self._session, user), self._visitors_xpb,
                self._visitors_current_page_xpb, self._visitors_total_page_xpb,
            )
        )

        #: A :class:`~okcupyd.question.Questions` object that is instantiated
        #: with the owning :class:`~.User` instance's session.
        self.questions = Questions(self._session)

        #: An :class:`~okcupyd.attractiveness_finder.AttractivenessFinder`
        #: object that is instantiated with the owning :class:`~.User`
        #: instance's session.
        self.attractiveness_finder = AttractivenessFinder(self._session)

        #: A :class:`~okcupyd.photo.PhotoUploader` that is instantiated with
        #: the owning :class:`~.User` instance's session.
        self.photo = PhotoUploader(self._session)

    def get_profile(self, username):
        """Get the :class:`~okcupyd.profile.Profile` associated with the supplied
        username.

        :param username: The username of the profile to retrieve.
        """
        return self._session.get_profile(username)

    @property
    def username(self):
        """Return the username associated with the :class:`.User`."""
        return self.profile.username

    def message(self, username, message_text):
        """Message an okcupid user. If an existing conversation between the
        logged in user and the target user can be found, reply to that thread
        instead of starting a new one.

        :param username: The username of the user to which the message should
                         be sent.
        :param message_text: The body of the message.

        """
        # Try to reply to an existing thread.
        if not isinstance(username, six.string_types):
            username = username.username
        for thread in sorted(set(self.inbox + self.outbox),
                             key=lambda t: t.datetime, reverse=True):
            if thread.correspondent.lower() == username.lower():
                thread.reply(message_text)
                return

        return self._message_sender.send(username, message_text)

    def search(self, **kwargs):
        """Call :func:`~okcupyd.search.SearchFetchable`  to get a
        :class:`~okcupyd.util.fetchable.Fetchable` object that will lazily
        perform okcupid searches to provide :class:`~okcupyd.profile.Profile`
        objects matching the search criteria.

        Defaults for `gender`, `gentation`, `location` and `radius` will
        be provided if none are given.

        :param kwargs: See the :func:`~okcupyd.search.SearchFetchable`
                       docstring for details about what parameters are
                       available.
        """
        kwargs.setdefault('gender', self.profile.gender[0])
        gentation = helpers.get_default_gentation(self.profile.gender,
                                                  self.profile.orientation)
        kwargs.setdefault('gentation', gentation)
        kwargs.setdefault('location', self.profile.location)
        kwargs.setdefault('radius', 25)
        if 'count' in kwargs:
            count = kwargs.pop('count')
            return search(session=self._session, count=count, **kwargs)
        return SearchFetchable(self._session, **kwargs)

    def quickmatch(self):
        """Return a :class:`~okcupyd.profile.Profile` obtained by visiting the
        quickmatch page.
        """
        response = self._session.okc_get('quickmatch', params={'okc_api': 1})
        return Profile(self._session, response.json()['sn'])

    def copy(self, profile_or_user):
        """Create a :class:`~okcupyd.profile_copy.Copy` instance with the
        provided object as the source and this :class:`~okcupyd.user.User`
        as the destination.

        :param profile_or_user: A :class:`~okcupyd.user.User` or
                                :class:`~okcupyd.profile.Profile` object.
        """
        return Copy(profile_or_user, self)

    def __repr__(self):
        return 'User("{0}")'.format(self.profile.username)
