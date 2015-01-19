import itertools
import logging

import simplejson

from . import helpers
from . import magicnumbers
from . import util
from . import filter
from .profile import Profile
from .session import Session
from .xpath import xpb


log = logging.getLogger(__name__)

#: A :class:`~okcupyd.filter.Filters` object that stores all of the
#: filters that are accepted by :func:`.SearchFetchable`.
search_filters = filter.Filters()
search_filters.register_filter_builder(
    filter.gentation_filter,
    descriptions="The gentation of returned search results.",
    acceptable_values=magicnumbers.gentation_to_number.keys(),
    types=str
)
search_filters.register_filter_builder(
    filter.location_filter,
    types=int,
    descriptions=("The maximum distance from the specified location of "
                  "returned search results.")
)
search_filters.register_filter_builder(
    filter.age_filter,
    decider=filter.Filters.any_not_none_decider,
    types=(int, int),
    descriptions=['The minimum age of returned search results.',
                  'The maximum age of returned search results.']
)
search_filters.register_filter_builder(
    magicnumbers.get_kids_filter,
    keys=('has_kids', 'wants_kids'),
    acceptable_values=(magicnumbers.maps.has_kids.pattern_to_value.keys(),
                       magicnumbers.maps.wants_kids.pattern_to_value.keys()),
    decider=filter.Filters.any_decider
)
search_filters.register_filter_builder(
    magicnumbers.get_question_filter,
    decider=filter.Filters.any_not_none_decider,
    types=(':class:`~okcupyd.question.UserQuestion`', list),
    descriptions=["A question whose answer should be used to match search "
                  "results, or a question id. If a question id, "
                  "`question_answers` must be supplied.",
                  "A list of acceptable question answer indices."]
)
search_filters.register_filter_builder(
    magicnumbers.get_language_query,
    keys=('language',),
    acceptable_values=list(magicnumbers.language_map.keys())
)
search_filters.register_filter_builder(
    magicnumbers.get_join_date_filter,
    types=int,
    acceptable_values=magicnumbers.join_date_string_to_int.keys()
)


@search_filters.register_filter_builder(
    decider=search_filters.any_decider,
    types=(int, int),
    descriptions=["The minimum attractiveness of returned search results.",
                  "The maximum attractiveness of returned search results."]
)
def attractiveness_filter(attractiveness_min, attractiveness_max):
    if attractiveness_min == None:
        attractiveness_min = 0
    if attractiveness_max == None:
        attractiveness_max = 10000
    return '25,{0},{1}'.format(attractiveness_min, attractiveness_max)


@search_filters.register_filter_builder(
    types=int,
    descriptions=("The minimum number of questions answered by returned search "
                  "results."),
)
def question_count_filter(question_count_min):
    return '33,{0}'.format(question_count_min)


search_filters.register_filter_builder(
    magicnumbers.get_height_filter,
    descriptions=["The minimum height of returned search results.",

                  "The maximum height of returned search results."],
    acceptable_values=[["A height int in inches",
                       "An imperial height string e.g. 5'4\"",
                       "A metric height string e.g. 1.54m"] for _ in range(2)],
    decider=search_filters.any_not_none_decider
)


@search_filters.register_filter_builder(
    acceptable_values=('day', 'today', 'week', 'month', 'year', 'decade'),
    types=str
)
def last_online_filter(last_online):
    return '5,{0}'.format(helpers.format_last_online(last_online))


@search_filters.register_filter_builder(
    types=str,
    acceptable_values=('not single', 'married', 'single', 'any'),
    descriptions="The relationship status of returned search results."
)
def status_filter(status):
    status_int = 2  # single, default
    if status.lower() in ('not single', 'married'):
        status_int = 12
    elif status.lower() == 'any':
        status_int = 0
    return '35,{0}'.format(status_int)


def build_option_filter(key):
    @search_filters.register_filter_builder(
        keys=(key,),
        acceptable_values=magicnumbers.maps[key].pattern_to_value.keys(),
        types=str
    )
    @util.makelist_decorator
    def option_filter(value):
        return magicnumbers.filters[key](value)
for key in ['smokes', 'drinks', 'drugs', 'education_level', 'job',
            'income', 'religion', 'monogamy', 'diet', 'sign',
            'ethnicities', 'cats', 'dogs', 'bodytype']:
    build_option_filter(key)


class MatchCardExtractor(object):

    def __init__(self, div):
        self._div = div

    _id_xpb = xpb.button.with_classes(
        "binary_rating_button"
    ).select_attribute_('data-tuid')

    @property
    def id(self):
        return int(self._id_xpb.one_(self._div))

    @property
    def username(self):
        return xpb.div.with_class('username').get_text_(self._div).strip()

    @property
    def age(self):
        return int(xpb.span.with_class('age').get_text_(self._div))

    @property
    def location(self):
        return helpers.replace_chars(
            xpb.span.with_class('location').get_text_(self._div)
        )

    _match_percentage_xpb = xpb.div.with_classes('percentage_wrapper', 'match').\
                            span.with_classes('percentage')

    @property
    def match_percentage(self):
        try:
            return int(self._match_percentage_xpb.get_text_(self._div).strip('%'))
        except:
            return 0

    _enemy_percentage_xpb = xpb.div.with_classes('percentage_wrapper', 'enemy').\
                            span.with_classes('percentage').text_

    @property
    def enemy_percentage(self):
        try:
            return int(self._enemy_percentage_xpb.one_(self._div).strip('%'))
        except:
            return None

    @property
    def contacted(self):
        return bool(xpb.div.with_class('fancydate').apply_(self._div))

    @property
    def as_dict(self):
        return {
            # TODO(@IvanMalison): add rating.
            'username': self.username,
            'age': self.age,
            'location': self.location,
            'id': self.id,
            'contacted': self.contacted,
            'match_percentage': self.match_percentage,
            'enemy_percentage': self.enemy_percentage
        }


_match_card_xpb = xpb.div.with_classes('match_card')
# The docstring below is extended automatically. Read it in its entirety at
# http://okcupyd.readthedocs.org/en/latest/ or by generating the documentation
# yourself.
def SearchFetchable(session=None, **kwargs):
    """Search okcupid.com with the given parameters. Parameters are registered
    to this function through :meth:`~okcupyd.filter.Filters.register_filter_builder`
    of :data:`~okcupyd.search.search_filters`.

    :returns: A :class:`~okcupyd.util.fetchable.Fetchable` of
              :class:`~okcupyd.profile.Profile` instances.

    :param session: A logged in session.
    :type session: :class:`~okcupyd.session.Session`
    :param location: A location string which will be used to filter results.
    :param gender: The gender of the user performing the search.
    :param keywords: A list or space delimeted string of words to search for.
    :param order_by: The criteria to use for ordering results. expected_values:
                     'match', 'online', 'special_blend'
    """
    session = session or Session.login()
    return util.Fetchable.fetch_marshall(
        SearchHTMLFetcher(session, **kwargs),
        util.SimpleProcessor(
            session,
            lambda match_card_div: Profile(
                session=session,
                **MatchCardExtractor(match_card_div).as_dict
            ),
            _match_card_xpb
        )
    )


class SearchHTMLFetcher(object):

    _username_xpb = xpb.div.with_class('username')

    def __init__(self, session=None, **options):
        self._session = session or Session.login()
        self._options = options
        self.location = self._options.pop('location', None)
        self.gender = self._options.pop('gender', 'm')
        self.keywords = self._options.pop('keywords', None)
        self.order_by = self._options.pop('order_by', 'match').upper()
        self.count = self._options.pop('count', 9)
        self.filters = search_filters.build(**self._options)

    def _query_params(self, low=None):
        search_parameters = {
            'timekey': 1,
            'matchOrderBy': self.order_by.upper(),
            'custom_search': '0',
            'fromWhoOnline': '0',
            'mygender': self.gender,
            'update_prefs': '1',
            'sort_type': '0',
            'sa': '1',
            'count': self.count,
            'locid': (str(helpers.get_locid(self._session, self.location))
                      if self.location else 0),
            'ajax_load': 1,
            'discard_prefs': 1,
            'match_card_class': 'just_appended'
        }
        if low:
            search_parameters['low'] = low
        if self.keywords: search_parameters['keywords'] = self.keywords
        search_parameters.update(self.filters)
        return search_parameters

    def fetch(self, start_at=None, count=None):
        search_parameters = self._query_params(low=start_at)
        log.info(simplejson.dumps({'search_parameters': search_parameters}))
        response = self._session.okc_get('match',
                                         params=search_parameters)
        try:
            search_html = response.json()['html']
        except:
            log.warning(simplejson.dumps({'failure': response.content}))
            raise
        return search_html

    def __unicode__(self):
        return u'{0}({1})'.format(type(self).__name__, repr(self._options))

    __repr__ = __unicode__


def search(session=None, count=1, **kwargs):
    return SearchFetchable(session, count=count, **kwargs)[:count]


SearchFetchable.__doc__ = '\n    '.join(
    itertools.chain(
        [SearchFetchable.__doc__], search_filters.build_documentation_lines()
    )
)
