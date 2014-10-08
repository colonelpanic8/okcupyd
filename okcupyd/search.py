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
    types=int,
    descriptions=['The minimum age of returned search results.',
                  'The maximum age of returned search results.']
)


@search_filters.register_filter_builder(
    decider=search_filters.any_decider,
    types=int,
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
    decider=search_filters.any_not_none_decider
)
def height_filter(height_min, height_max):
    return magicnumbers.get_height_query(height_min, height_max)


@search_filters.register_filter_builder
def last_online_filter(last_online):
    return '5,{0}'.format(helpers.format_last_online(last_online))


@search_filters.register_filter_builder
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
        acceptable_values=magicnumbers.binary_lists[key],
        types=str
    )
    @util.makelist_decorator
    def option_filter(value):
        return magicnumbers.get_options_query(key, value)


for key in ['smokes', 'drinks', 'drugs', 'education', 'job',
            'income', 'religion', 'monogamy', 'diet', 'sign',
            'ethnicity']:
    build_option_filter(key)


         # ('offspring', util.makelist_decorator(magicnumbers.get_kids_query)),
         # ('join_date', magicnumbers.get_join_date_query),
         # ('languages', magicnumbers.get_language_query)]

# search_filters.register_filter_builder(
#     util.makelist_decorator(magicnumbers.get_pet_queries)),
# keys=('pets',),
#     types=str,
# )


_username_xpb = xpb.div.with_classes('match_card').\
                div.with_class('username').a.text_
def SearchFetchable(session=None, **kwargs):
    """Search okcupid.com with the given parameters.

    :returns: A :class:`okcupyd.util.fetchable.Fetchable` of
              :class:`okcupyd.profile.Profile` instances.
    """

    session = session or Session.login()
    return util.Fetchable.fetch_marshall(
        SearchHTMLFetcher(session, **kwargs),
        util.SimpleProcessor(
            session,
            lambda username: Profile(session, username.strip()),
            _username_xpb
        )
    )


SearchFetchable.__doc__ += '\n' + search_filters.build_documentation()


class SearchHTMLFetcher(object):

    _username_xpb = xpb.div.with_class('username')

    def __init__(self, session=None, **options):
        self._session = session or Session.login()
        self._options = options

    @property
    def location(self):
        return self._options.get('location', None)

    @property
    def gender(self):
        return self._options.get('gender', 'm')

    @property
    def keywords(self):
        return self._options.get('keywords')

    @property
    def order_by(self):
        return self._options.get('order_by', 'match').upper()

    def _query_params(self, count=None, low=None):
        search_parameters = {
            'timekey': 1,
            'matchOrderBy': self.order_by,
            'custom_search': '0',
            'fromWhoOnline': '0',
            'mygender': self.gender,
            'update_prefs': '1',
            'sort_type': '0',
            'sa': '1',
            'count': str(count) if count else self._options.get('count', 9),
            'locid': (str(helpers.get_locid(self._session, self.location))
                      if self.location else 0),
            'ajax_load': 1,
            'discard_prefs': 1,
            'match_card_class': 'just_appended'
        }
        if low:
            search_parameters['low'] = low
        if self.keywords: search_parameters['keywords'] = self.keywords
        search_parameters.update(search_filters.build(**self._options))
        return search_parameters

    def fetch(self, start_at=None, count=None):
        search_parameters = self._query_params(low=start_at, count=count)
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
