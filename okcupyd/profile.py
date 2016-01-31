import datetime
import logging

from lxml import html
import simplejson

from . import details
from . import essay
from . import helpers
from . import looking_for
from . import util
from .question import QuestionFetcher
from .xpath import xpb


log = logging.getLogger(__name__)


class Profile(object):
    """Represent the profile of an okcupid user.

    Many of the attributes on this object are
    :class:`~okcupyd.util.cached_property` instances which lazily load their
    values, and cache them once they have been accessed. This makes it so
    that this object avoids making unnecessary HTTP requests to retrieve the
    same piece of information twice.

    Because of this caching behavior, care must
    be taken to invalidate cached attributes on the object if an up to date view
    of the profile is needed. It is recommended that you call :meth:`.refresh`
    to accomplish this, but it is also possible to use
    :meth:`~okcupyd.util.cached_property.bust_self` to bust individual
    properties if necessary.
    """

    def __init__(self, session, username, **kwargs):
        """
        :param session: A logged in :class:`~okcupyd.session.Session`
        :param username: The username associated with the profile.
        """
        self._session = session
        #: The username of the user to whom this profile belongs.
        self.username = username
        #: A :class:`~okcupyd.util.fetchable.Fetchable` of
        #: :class:`~okcupyd.question.Question` instances, each corresponding
        #: to a question that has been answered by the user to whom this
        #: profile belongs.
        #: The fetchable consists of :class:`~okcupyd.question.UserQuestion`
        #: instead when the profile belongs to the logged in user.
        self.questions = self.question_fetchable()
        #: A :class:`~okcupyd.details.Details` instance belonging to the same
        #: user that this profile belongs to.
        self.details = details.Details(self)

        if kwargs:
            self._set_cached_properties(kwargs)

    def _set_cached_properties(self, values):
        property_names = set(
            name for name, _ in util.cached_property.get_cached_properties(self)
        )
        for key, value in values.items():
            if key not in property_names:
                log.warning("Unrecognized kwarg {0} with value {1} "
                            "passed to Profile constructor.")
            self.__dict__[key] = value

    def refresh(self, reload=False):
        """
        :param reload: Make the request to return a new profile tree. This will
                       result in the caching of the profile_tree attribute. The
                       new profile_tree will be returned.
        """
        util.cached_property.bust_caches(self, excludes=('authcode'))
        self.questions = self.question_fetchable()
        if reload:
            return self.profile_tree

    @property
    def is_logged_in_user(self):
        """
        :returns: `True` if this profile and the session it was created with
                   belong to the same user and False otherwise."""
        return self._session.log_in_name.lower() == self.username.lower()

    @util.cached_property
    def _profile_response(self):
        return self._session.okc_get(
            u'profile/{0}'.format(self.username)
        ).content

    @util.cached_property
    def profile_tree(self):
        """
        :returns: a :class:`lxml.etree` created from the html of the profile
                  page of the account associated with the username that this
                  profile was insantiated with.
        """
        return html.fromstring(self._profile_response)

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

    @util.cached_property
    def authcode(self):
        return helpers.get_authcode(self.profile_tree)

    _photo_info_xpb = xpb.div.with_class('photo').img.select_attribute_('src')
    @util.cached_property
    def photo_infos(self):
        """
        :returns: list of :class:`~okcupyd.photo.Info` instances for each photo
                  displayed on okcupid.
        """
        from . import photo
        pics_request = self._session.okc_get(
            u'profile/{0}/album/0'.format(self.username),
        )
        pics_tree = html.fromstring(u'{0}{1}{2}'.format(
            u'<div>', pics_request.json()['fulls'], u'</div>'
        ))
        return [photo.Info.from_cdn_uri(uri)
                for uri in self._photo_info_xpb.apply_(pics_tree)]


    @util.cached_property
    def looking_for(self):
        """
        :returns: A :class:`~okcupyd.looking_for.LookingFor` instance associated
                  with this profile.
        """
        return looking_for.LookingFor(self)

    _liked_xpb = xpb.button.with_class('binary_rating_button')

    @property
    def rating(self):
        """
        Deprecated. Use :meth:`.liked` instead.

        :returns: the rating that the logged in user has given this user or
                  0 if no rating has been given.
        """
        return 5 if self.liked else 0

    @util.cached_property
    def liked(self):
        """
        :returns: Whether or not the logged in user liked this profile
        """
        if self.is_logged_in_user: return False
        classes = self._liked_xpb.one_(self.profile_tree).attrib['class'].split()
        return 'liked' in classes

    _contacted_xpb = xpb.div.with_class('actions2015').button.\
                     with_classes('actions2015-chat', 'flatbutton', 'blue').\
                     select_attribute_('data-tooltip')

    @util.cached_property
    def contacted(self):
        """
        :retuns: A boolean indicating whether the logged in user has contacted
                 the owner of this profile.
        """
        try:
            contacted_span = self._contacted_xpb.one_(self.profile_tree)
        except:
            return False
        else:
            timestamp = contacted_span.replace('Last contacted ', '')
            return helpers.parse_date_updated(timestamp)

    @util.cached_property
    def responds(self):
        """
        :returns: The frequency with which the user associated with this profile
                  responds to messages.
        """
        contacted_text = self._contacted_xpb.\
                         get_text_(self.profile_tree).lower()
        if 'contacted' not in contacted_text:
            return contacted_text.strip().replace('replies ', '')

    _id_xpb = xpb.button.with_class('binary_rating_button').\
              select_attribute_("data-tuid")

    @util.cached_property
    def id(self):
        """
        :returns: The id that okcupid.com associates with this profile.
        """
        if self.is_logged_in_user: return self._current_user_id
        return int(self._id_xpb.one_(self.profile_tree))

    @util.cached_property
    def _current_user_id(self):
        return int(helpers.get_id(self.profile_tree))

    @util.cached_property
    def essays(self):
        """
        :returns: A :class:`~okcupyd.essay.Essays` instance that is
                  associated with this profile.
        """
        return essay.Essays(self)

    _age_xpb = xpb.span.with_class('userinfo2015-basics-asl-age')
    _user_age_xpb = xpb.span(id='ajax_age')

    @util.cached_property
    def age(self):
        """
        :returns: The age of the user associated with this profile.
        """
        if self.is_logged_in_user: 
            # Retrieve the logged-in user's profile age
            return int(self._user_age_xpb.get_text_(self.profile_tree).strip())
        else:
            # Retrieve a non logged-in user's profile age
            return int(self._age_xpb.get_text_(self.profile_tree))

    _percentages_and_ratings_xpb = xpb.div.with_class('matchanalysis2015-graphs')

    @util.cached_property
    def match_percentage(self):
        """
        :returns: The match percentage of the logged in user and the user
                  associated with this object.
        """
        return int(self._percentages_and_ratings_xpb.
                   div.with_class('matchgraph--match').
                   div.with_class('matchgraph-graph').
                   canvas.select_attribute_('data-pct').
                   one_(self.profile_tree))

    @util.cached_property
    def enemy_percentage(self):
        """
        :returns: The enemy percentage of the logged in user and the user
                  associated with this object.
        """
        return int(self._percentages_and_ratings_xpb.
                   div.with_class('matchgraph--enemy').
                   div.with_class('matchgraph-graph').
                   canvas.select_attribute_('data-pct').
                   one_(self.profile_tree))

    _location_xpb = xpb.span.with_class('userinfo2015-basics-asl-location')
    _user_location_xpb = xpb.span(id='ajax_location')

    @util.cached_property
    def location(self):
        """
        :returns: The location of the user associated with this profile.
        """
        if self.is_logged_in_user: 
            # Retrieve the logged-in user's profile location
            return self._user_location_xpb.get_text_(self.profile_tree)
        else:
            # Retrieve a non logged-in user's profile location
            return self._location_xpb.get_text_(self.profile_tree)

    @util.cached_property
    def gender(self):
        """The gender of the user associated with this profile."""
        return xpb.span.with_class('ajax_gender').get_text_(self.profile_tree)

    @util.cached_property
    def orientation(self):
        """The sexual orientation of the user associated with this profile."""
        return xpb.dd(id='ajax_orientation').\
            get_text_(self.profile_tree).strip()

    @util.curry
    def message(self, message, thread_id=None):
        """Message the user associated with this profile.

        :param message: The message to send to this user.
        :param thread_id: The id of the thread to respond to, if any.
        """
        return_value = helpers.Messager(self._session).send(
            self.username, message, self.authcode, thread_id
        )
        self.refresh(reload=False)
        return return_value

    @util.cached_property
    def attractiveness(self):
        """
        :returns: The average attractiveness rating given to this profile by the
                  okcupid.com community.
        """
        # This has to be here to avoid a circular import for now.
        from .attractiveness_finder import AttractivenessFinder
        return AttractivenessFinder(self._session)(self.username)

    def toggle_like(self):
        """Toggle whether or not the logged in user likes this profile."""
        return self.rate(1 if self.liked else 5)

    def like(self):
        """Like this profile."""
        return self.rate(5)

    def unlike(self):
        """Unlike this profile."""
        return self.rate(1)

    def rate(self, rating):
        """Rate this profile as the user that was logged in with the session
        that this object was instantiated with.

        :param rating: The rating to give this user.
        """
        parameters = {
            'voterid': self._current_user_id,
            'target_userid': self.id,
            'type': 'vote',
            'cf': 'profile2',
            'target_objectid': 0,
            'vote_type': 'personality',
            'score': rating,
        }
        response = self._session.okc_post('vote_handler',
                                          data=parameters)
        response_json = response.json()
        log_function = log.info if response_json.get('status', False) \
                       else log.error
        log_function(simplejson.dumps({'rate_response': response_json,
                                       'sent_parameters': parameters,
                                       'headers': dict(self._session.headers)}))
        self.refresh(reload=False)

    def find_question(self, question_id, question_fetchable=None):
        """
        :param question_id: The id of the question to search for
        :param question_fetchable: The question fetchable to iterate through
                                   if none is provided `self.questions`
                                   will be used.
        """
        question_fetchable = question_fetchable or self.questions
        for question in question_fetchable:
            if int(question.id) == int(question_id):
                return question

    def question_fetchable(self, **kwargs):
        """
        :returns: A :class:`~okcupyd.util.fetchable.Fetchable` instance that
                  contains objects representing the answers that the user
                  associated with this profile has given to okcupid.com match
                  questions.
        """
        return util.Fetchable(QuestionFetcher(
            self._session, self.username,
            is_user=self.is_logged_in_user, **kwargs
        ))

    def authcode_get(self, path, **kwargs):
        """Perform an HTTP GET to okcupid.com using this profiles session
        where the authcode is automatically added as a query parameter.
        """
        kwargs.setdefault('params', {})['authcode'] = self.authcode
        return self._session.okc_get(path, **kwargs)

    def authcode_post(self, path, **kwargs):
        """Perform an HTTP POST to okcupid.com using this profiles session
        where the authcode is automatically added as a form item.
        """
        kwargs.setdefault('data', {})['authcode'] = self.authcode
        return self._session.okc_post(path, **kwargs)

    def __eq__(self, other):
        self.username.lower() == other.username.lower()

    def __repr__(self):
        return u'{0}("{1}")'.format(type(self).__name__, self.username)
