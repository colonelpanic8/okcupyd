import collections
import datetime
import logging
import re

from lxml import html
import simplejson

from . import helpers
from . import magicnumbers
from . import util
from .filter import Filters
from .question import QuestionFetcher
from .xpath import xpb


log = logging.getLogger(__name__)


class LookingFor(object):

    Ages = collections.namedtuple('ages', ('min', 'max'))
    _ages_re = re.compile(u'Ages ([0-9]{1,3})\u2013([0-9]{1,3})')

    _looking_for_xpb = xpb.div.with_classes('text', 'what_i_want')

    def __init__(self, profile):
        self._profile = profile

    @util.cached_property
    def raw_fields(self):
        li_elements = self._looking_for_xpb.li.apply_(
            self._profile.profile_tree
        )
        return {li.attrib['id'].split('_')[1]: li.text_content()
                for li in li_elements}

    def update_property(function):
        @property
        def wrapped(self):
            return function(self)

        @wrapped.setter
        def wrapped_setter(self, value):
            self.update(**{function.__name__: value})

        return wrapped_setter

    @update_property
    def gentation(self):
        return self.raw_fields.get('gentation').lower()

    @update_property
    def ages(self):
        match = self._ages_re.match(self.raw_fields.get('ages'))
        return self.Ages(int(match.group(1)), int(match.group(2)))

    @update_property
    def single(self):
        return 'display: none;' not in self._looking_for_xpb.li(id='ajax_single').\
            one_(self._profile.profile_tree).attrib['style']

    @update_property
    def near_me(self):
        return 'near' in self.raw_fields.get('near', '').lower()

    @update_property
    def kinds(self):
        return self.raw_fields.get('lookingfor', '').replace('For', '').strip().split(', ')

    def update(self, ages=None, single=None, near_me=None, kinds=None,
               gentation=None):
        ages = ages or self.ages
        single = single or self.single
        near_me = near_me or self.near_me
        kinds = kinds or self.kinds
        data = {
            'okc_api': '1',
            'searchprefs.submit': '1',
            'update_prefs': '1',
            'lquery': '',
            'locid': '0',
            'filter4': '1,1',
            'filter5': '7,1'
        }
        if kinds:
            kinds_numbers = self._build_kinds_numbers(kinds)
            if kinds_numbers:
                data['lookingfor'] = kinds_numbers[0]
        age_min, age_max = ages
        data.update(Filters(status='single' if single else 'any',
                            gentation=gentation,
                            age_min=age_min, age_max=age_max,
                            radius=25 if near_me else 0).build())
        log.info(simplejson.dumps({'looking_for_update': data}))
        util.cached_property.bust_caches(self)
        response = self._profile.authcode_get('profileedit2', params=data)
        self._profile.refresh(reload=False)
        return response.content

    @staticmethod
    def _build_kinds_numbers(looking_for_items):
        looking_for_numbers = []
        if not isinstance(looking_for_items, collections.Iterable):
            looking_for_numbers = (looking_for_items,)
        for item in looking_for_items:
            for matcher, number in magicnumbers.looking_for_re_numbers:
                if matcher.search(item) is not None:
                    looking_for_numbers.append(number)
        return looking_for_numbers

    del update_property


class Essays(object):
    """Interface to reading and writing a users essays."""

    @staticmethod
    def build_essay_property(essay_index, essay_name):
        essay_xpb = xpb.div(id='essay_{0}'.format(essay_index))
        essay_text_xpb = essay_xpb.div.with_class('text').div.with_class('essay')
        @property
        def essay(self):
            try:
                essay_text = essay_text_xpb.get_text_(self._essays).strip()
            except IndexError:
                return None
            if essay_name not in self._short_name_to_title:
                self._short_name_to_title[essay_name] = helpers.replace_chars(
                    essay_xpb.a.with_class('essay_title').get_text_(
                        self._profile.profile_tree
                    )
                )
            return essay_text

        @essay.setter
        def set_essay_text(self, essay_text):
            self._submit_essay(essay_index, essay_text)

        return set_essay_text

    @classmethod
    def _init_essay_properties(cls):
        for essay_index, essay_name in enumerate(cls.essay_names):
            setattr(cls, essay_name,
                    cls.build_essay_property(essay_index, essay_name))

    _essays_xpb = xpb.div(id='main_column')
    #: A list of the attribute names that are used to store the text of
    #: of essays on instances of this class.
    essay_names = ['self_summary', 'my_life', 'good_at', 'people_first_notice',
                   'favorites', 'six_things', 'think_about', 'friday_night',
                   'private_admission', 'message_me_if']

    def __init__(self, profile):
        """:param profile: A :class:`.Profile`"""
        self._profile = profile
        self._short_name_to_title = {}

    @property
    def short_name_to_title(self):
        for i in self: pass # Make sure that all essays names have been retrieved
        return self._short_name_to_title

    @util.cached_property
    def _essays(self):
        return self._essays_xpb.one_(self._profile.profile_tree)

    def _submit_essay(self, essay_id, essay_body):
        self._profile.authcode_post('profileedit2', data={
            "essay_id": essay_id,
            "essay_body": essay_body,
            "okc_api": 1
        })
        self.refresh()

    def refresh(self):
        self._profile.refresh()
        util.cached_property.bust_caches(self)

    def __iter__(self):
        for essay_name in self.essay_names:
            yield getattr(self, essay_name)


Essays._init_essay_properties()


_profile_details_xpb = xpb.div.with_classes('profile_details')
def detail(name, setter=False):
    dd_xpb = _profile_details_xpb.dd(id='ajax_{0}'.format(name))
    @property
    def detail_property(self):
        dd_xpb.get_text_(self.profile_tree)
    if setter:
        return detail_property.setter
    return detail_property


class Details(object):

    def __init__(self, session, profile_tree):
        self._session = session
        self.profile_tree = profile_tree


class Profile(object):
    """Represent the profile of an okcupid user.
    Many of the attributes on this object are
    :class:`okcupyd.util.cached_property` instances which lazily load their
    values, and cache them once they have been accessed. This avoids makes it so
    that this object avoids making unnecessary HTTP requests to retrieve the
    same piece of information twice. Because of this caching behavior, care must
    be taken to invalidate cached attributes on the object if an up to date view
    of the profile is needed. It is recommended that you call :meth:`refresh` to
    accomplish this, but it is also possible to use
    :meth:`okcupyd.util.cached_property.bust_self` to bust individual methods if
    necessary.
    """

    def __init__(self, session, username):
        """
        :param session: A logged in :class:`okcupyd.session.Session`
        :param username: The username associated with the profile.
        """
        self._session = session
        self.username = username
        self.questions = self.question_fetchable()

    def refresh(self, reload=False):
        """
        :param reload: Make the request to return a new profile tree. This will
                       result in the caching of the profile_tree attribute. The
                       new profile_tree will be returned.
        """
        util.cached_property.bust_caches(self)
        self.questions = self.question_fetchable()
        if reload:
            return self.profile_tree

    @property
    def is_logged_in_user(self):
        """Return True if this profile and the session it was created with
        belong to the same user and False otherwise."""
        return self._session.log_in_name.lower() == self.username.lower()

    @util.cached_property
    def _profile_response(self):
        return self._session.okc_get(u'profile/{0}'.format(self.username)).content

    @util.cached_property
    def profile_tree(self):
        """Return a :class:`lxml.etree` created from the html of the profile page
        of the account associated with the username that this profile was
        insantiated with.
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

    @util.cached_property
    def photo_infos(self):
        """Return a list containing a :class:`okcupyd.photo.Info` instance
        for each picture that the owner of this profile displays on okcupid.
        """
        pics_request = self._session.okc_get(
            u'profile/{0}/photos#0'.format(self.username)
        )
        pics_tree = html.fromstring(pics_request.content.decode('utf8'))
        from . import photo
        return map(photo.Info.from_cdn_uri,
                   xpb.div(id='album_0').img.select_attribute_('src',
                                                               pics_tree))

    @util.cached_property
    def looking_for(self):
        """Return a :class:`.LookingFor` instance associated with this profile.
        """
        return LookingFor(self)

    _rating_xpb = xpb.div(id='rating').ul(id='personality-rating').li.\
                  with_class('current-rating')

    @util.cached_property
    def rating(self):
        """Return the rating that the logged in user has given this user or
        0 if no rating has been given.
        """
        if self.is_logged_in_user: return 0
        rating_style = self._rating_xpb.select_attribute_('style').one_(
            self.profile_tree
        )
        width_percentage = int(''.join(c for c in rating_style if c.isdigit()))
        return width_percentage // 20

    _contacted_xpb = xpb.div(id='actions').div.with_classes('tooltip_text',
                                                               'hidden')

    @util.cached_property
    def contacted(self):
        """Return a boolean indicating whether the logged in user has contacted
        the owner of this profile.
        """
        try:
            contacted_span = self._contacted_xpb.span.with_class('fancydate').\
                             one_(self.profile_tree)
        except:
            return False
        else:
            timestamp = contacted_span.attrib['id'].split('_')[-1][:-2]
            return datetime.datetime.fromtimestamp(int(timestamp[:10]))

    @util.cached_property
    def responds(self):
        """The frequency with which the user associated with this profile
        responds to messages.
        """
        contacted_text = self._contacted_xpb.get_text_(self.profile_tree).lower()
        if 'contacted' not in contacted_text:
            return contacted_text.strip().replace('replies ', '')

    @util.cached_property
    def id(self):
        """The id that okcupid.com associates with this profile."""
        if self.is_logged_in_user: return self._current_user_id
        return int(self._rating_xpb.select_attribute_('id').
                   one_(self.profile_tree).split('-')[-2])

    @util.cached_property
    def _current_user_id(self):
        return int(helpers.get_id(self.profile_tree))

    @util.cached_property
    def essays(self):
        """An :class:`.Essays` instance that is associated with this profile."""
        return Essays(self)

    @util.cached_property
    def age(self):
        """The age of the user associated with this profile."""
        return int(xpb.span(id='ajax_age').get_text_(self.profile_tree).strip())

    _percentages_and_ratings_xpb = xpb.div(id='percentages_and_ratings')

    @util.cached_property
    def match_percentage(self):
        """The match percentage of the logged in user and the user associated
        with this object.
        """
        return int(self._percentages_and_ratings_xpb.
                   div.with_class('match').
                   span.with_class('percent').
                   get_text_(self.profile_tree).strip('%'))

    @util.cached_property
    def enemy_percentage(self):
        """The enemy percentage of the logged in user and the user associated
        with this object.
        """
        return int(self._percentages_and_ratings_xpb.
                   div.with_class('enemy').
                   span.with_class('percent').
                   get_text_(self.profile_tree).strip('%'))

    @util.cached_property
    def location(self):
        """The location of the user associated with this profile."""
        return xpb.span(id='ajax_location').get_text_(self.profile_tree)

    @util.cached_property
    def gender(self):
        """The gender of the user associated with this profile."""
        return xpb.span(id='ajax_gender').get_text_(self.profile_tree)

    @util.cached_property
    def orientation(self):
        """The sexual orientation of the user associated with this profile."""
        return xpb.dd(id='ajax_orientation').get_text_(self.profile_tree).strip()

    _details_xpb = xpb.div(id='profile_details')

    @util.cached_property
    def details(self):
        details = {}
        details_div = self._details_xpb.one_(self.profile_tree)
        for dl in details_div.iter('dl'):
            title = dl.find('dt').text
            item = dl.find('dd')
            if title == 'Last Online' and item.find('span') is not None:
                details[title.lower()] = item.find('span').text.strip()
            elif title.lower() in details and len(item.text):
                details[title.lower()] = item.text.strip()
            else:
                continue
            details[title.lower()] = helpers.replace_chars(details[title.lower()])
        return details

    @util.curry
    def message(self, message, thread_id=None):
        """Message the user associated with this profile.
        :param message: The message to send to this user.
        :param thread_id: The id of the thread to respond to, if any.
        """
        return_value =  helpers.Messager(
            self._session
        ).send(self.username, message,
                       self.authcode, thread_id)
        self.refresh(reload=False)
        return return_value

    @util.cached_property
    def attractiveness(self):
        """The average attractiveness rating given to this profile by the
        okcupid.com community.
        """
        from .attractiveness_finder import AttractivenessFinder
        return AttractivenessFinder(self._session)(self.username)

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

    def question_fetchable(self, **kwargs):
        """Return a :class:`okcupyd.util.fetchable.Fetchable` instance that
        contains objects representing the answers that the user associated with
        this profile has given to okcupid.com match questions.
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
        return '{0}("{1}")'.format(type(self).__name__, self.username)
