import logging

import simplejson

from . import filter
from . import magicnumbers
from . import util
from .profile import Profile
from .session import Session
import six


log = logging.getLogger(__name__)


search_filters = filter.Filters()


def SearchFetchable(session=None, **kwargs):
    """Search okcupid.com with the given parameters. Parameters are
    registered to this function through
    :meth:`~okcupyd.filter.Filters.register_filter_builder` of
    :data:`~okcupyd.json_search.search_filters`.

    :returns: A :class:`~okcupyd.util.fetchable.Fetchable` of
              :class:`~okcupyd.profile.Profile` instances.

    :param session: A logged in session.
    :type session: :class:`~okcupyd.session.Session`
    :param order_by: Expected values: 'match', 'online', 'special_blend'
    """
    session = session or Session.login()
    return util.Fetchable(
        SearchManager(
            SearchJSONFetcher(session, **kwargs),
            ProfileBuilder(session)
        )
    )


class SearchManager(object):

    def __init__(self, search_fetchable, profile_builder):
        self._search_fetchable = search_fetchable
        self._profile_builder = profile_builder
        self._last_after = None

    def fetch(self, count=18):
        last_last_after = object()
        while last_last_after != self._last_after:
            last_last_after = self._last_after
            for profile in self.fetch_once(count=count):
                yield profile

    def fetch_once(self, count=18):
        response = self._search_fetchable.fetch(
            after=self._last_after, count=count
        )
        try:
            self._last_after = response['paging']['cursors']['after']
        except KeyError:
            log.warning(simplejson.dumps(
                {
                    'msg': "unable to get after cursor from response",
                    'response': response
                }
            )
        )
        for profile in self._profile_builder(response):
            yield profile


class SearchJSONFetcher(object):

    def __init__(self, session=None, order_by="MATCH", location=None, keywords=None, **options):
        self._session = session or Session.login()
        self._order_by = order_by.upper()
        if self._order_by not in ('MATCH', 'ONLINE', 'SPECIAL_BLEND'): # TODO: haven't verified that options other than 'MATCH' still work; the web interface no longer provides a way to modify this
            raise TypeError
        self._location = location # location string, haven't implemented
        self._keywords = keywords # list or space-delimited string of words to match, haven't implemented
        self._parameters = search_filters.build(**options)

    def _query_params(self, after=None, count=None):
        search_parameters = {
            'after': after,
            'limit': count,
            # other admin parameters
            'debug': 0,
            'username': "",
            'save_search': 1,
            'order_by': self._order_by,

            'i_want': None,
            'they_want': None,
            'tagOrder': [],

            # optional parameters
            'minimum_height': None,
            'maximum_height': None,
            'languages': 0,
            'speaks_my_language': 0, # TODO shall we make 1 the default?
            'ethnicity': [],
            'religion': [],
            'smoking': [],
            'drinking': [],
            'drugs': [],
            'education': [],
            'children': [],
            'interest_ids': [],
            'looking_for': [],
            'availability': "any",
            'monogamy': "unknown",
            'answers': [],

            # mandatory parameters
            'gender_tags': None,
            'orientation_tags': None.
            'minimum_age': 18,
            'maximum_age': 99,
            'located_anywhere': 0,
            'radius': 10, # TODO set from current user's profile?
            'gentation': [ 0 ], # TODO set from current user's profile?
            'last_login': 0,
            'lquery': "",
            'locid': 0, # FIXME what should default be?
            'location': None, # FIXME what should default be?
        }
        search_parameters.update(self._parameters)
        return {'_json': search_parameters}

    def fetch(self, after=None, count=18):
        search_parameters = self._query_params(after=after, count=count)
        log.info(simplejson.dumps({'search_parameters': search_parameters}))
        response = self._session.okc_get(
            'search', params=search_parameters
        )
        try:
            search_json = response.json()
        except:
            log.warning(simplejson.dumps({'failure': response.content}))
            raise
        return search_json


class ProfileBuilder(object):

    def __init__(self, session):
        self._session = session

    def __call__(self, response_dictionary):
        try:
            profile_infos = response_dictionary['data']
        except KeyError:
            log.warning(simplejson.dumps(
                {
                    'msg': "unable to get data from response",
                    'response': response_dictionary
                }
            )
        )
        else:
            for profile_info in profile_infos:
                yield Profile(self._session, profile_info["username"])


def accumulate_tags(keys, magicmap):
    acc = 0
    for k in keys:
        i = magicmap[k]
        if i is not None and i >= 0:
            acc += 2 ** i
        elif i < 0 or k.lower() in ('all', 'everyone', 'everybody', 'any'):
            acc = 0
            break
        else:
            raise TypeError
    return acc

# TODO also exploit `gender`?
class GenderFilter(search_filters.filter_class):
    output_key = "gender_tags"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", str)
    def transform(gender_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            if gent & (1+4+16):
                if gent & (2+8+32):
                    gender_sought = 'all'
                else:
                    gender_sought = 'men'
            elif gent & (2+8+32):
                gender_sought = 'women'
            else:
                gender_sought = 'all'
        return accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)

# TODO also exploit `gender`?
class OrientationFilter(search_filters.filter_class):
    output_key = "orientation_tags"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.orientation_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", str)
    def transform(orientation_sought, gentation):
        if gentation is not None:
            assert orientation_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            orientation_sought = []
            if gent & (1+2):
                orientation_sought.add('straight')
            if gent & (4+8):
                orientation_sought.add('gay')
            if gent & (16+32):
                orientation_sought.add('bisexual')
        return accumulate_tags(makelist(orientation_sought), magicnumbers.maps.orientation_tags)

# TODO also exploit `gender`?
class IWantFilter(search_filters.filter_class):
    output_key = "i_want"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", str)
    def transform(gender_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            if gent & (1+4+16):
                if gent & (2+8+32):
                    gender_sought = 'all'
                else:
                    gender_sought = 'men'
            elif gent & (2+8+32):
                gender_sought = 'women'
            else:
                gender_sought = 'all'
        gen = accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)
        if gen > 3:
            return 'other'
        assert gen >= 0
        return {0: 'everyone', 1:'women', 2:'men', 3:'other'}[gen]

# TODO also exploit `gender`?
class TheyWantFilter(search_filters.filter_class):
    output_key = "they_want"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.maps.orientation_tags.keys(),
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", "string or list of strings", str)
    def transform(gender_sought, orientation_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            assert orientation_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            if gent & (1+4+16):
                if gent & (2+8+32):
                    gender_sought = 'all'
                else:
                    gender_sought = 'men'
            elif gent & (2+8+32):
                gender_sought = 'women'
            else:
                gender_sought = 'all'
            orientation_sought = []
            if gent & (1+2):
                orientation_sought.add('straight')
            if gent & (4+8):
                orientation_sought.add('gay')
            if gent & (16+32):
                orientation_sought.add('bisexual')
        orient = accumulate_tags(makelist(orientation_sought), magicnumbers.maps.orientation_tags)
        if orient > 3:
            return 'other'
        gen = accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)
        if gen == 1:
            return {0: 'other', 1: 'men', 2: 'women', 3: 'other'}[orient]
        elif gen == 2:
            return {0: 'other', 1: 'women', 2: 'men', 3: 'other'}[orient]
        else:
            return 'other'

# TODO also exploit `gender`?
class GentationFilter(search_filters.filter_class):
    output_key = "gentation"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.maps.orientation_tags.keys(),
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", "string or list of strings", str)
    def transform(gender_sought, orientation_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            assert orientation_sought is None
            gentation = gentation.strip().lower()
        else:
            # convert gender_sought and orientation_sought to gentation
            gen = accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)
            orient = accumulate_tags(makelist(orientation_sought), magicnumbers.maps.orientation_tags)
            gentation = {
                # all genders
                0: {0: 'everybody', 1: 'everybody', 2: 'everybody', 3: 'everybody', 4: 'bi men and women',
                    5: 'everybody', 6: 'everybody', 7: 'everybody'},
                # women
                1: {0: 'women',
                    1: 'straight women only',
                    2: 'gay women only',
                    3: 'women',
                    4: 'bi women only',
                    5: 'women who like men',
                    6: 'women who like women',
                    7: 'women'},
                # men
                2: {0: 'men',
                    1: 'straight men only',
                    2: 'gay men only',
                    3: 'men',
                    4: 'bi men only',
                    5: 'men who like women',
                    6: 'men who like men',
                    7: 'men'},
                # women and men
                3: {0: 'everybody', 1: 'everybody', 2: 'everybody', 3: 'everybody', 4: 'bi men and women',
                    5: 'everybody', 6: 'everybody', 7: 'everybody'},
            }[gen & 3][orient & 7]
        return [magicnumbers.gentation_to_number.get(gentation, gentation)]




search_filters.add_to_docstring_of(SearchFetchable)
