import logging

import simplejson
import six

from . import filter
from . import magicnumbers
from . import util
from .profile import Profile
from .session import Session


log = logging.getLogger(__name__)


search_filters = filter.Filters(strict=False)


# The docstring below is extended automatically. Read it in its entirety at
# http://okcupyd.readthedocs.org/en/latest/ or by generating the documentation
# yourself.
def SearchFetchable(session=None, **kwargs):
    """Search okcupid.com with the given parameters. Parameters are
    registered to this function through
    :meth:`~okcupyd.filter.Filters.register_filter_builder` of
    :data:`~okcupyd.json_search.search_filters`.

    :returns: A :class:`~okcupyd.util.fetchable.Fetchable` of
              :class:`~okcupyd.profile.Profile` instances.

    :param session: A logged in session.
    :type session: :class:`~okcupyd.session.Session`
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
            ))
        for profile in self._profile_builder(response):
            yield profile


class SearchJSONFetcher(object):

    search_uri = '1/apitun/match/search'
    default_headers = {
        'Content-Type': 'application/json'
    }

    def __init__(self, session=None, **options):
        self._session = session or Session.login()
        self._options = options
        self._parameters = search_filters.build(session=self._session, **options)

    def _get_headers(self):
        headers = {
            "authorization": "Bearer {}".format(self._session.access_token)
        }
        headers.update(self.default_headers)
        return headers

    def _request_params(self, after=None, count=None):
        return {
            'headers': self._get_headers(),
            'data': simplejson.dumps(self._post_body(after, count)),
            'path': self.search_uri,
        }

    def _post_body(self, after=None, count=None):
        search_parameters = {
            'after': after,
            'limit': count,
            'fields': "userinfo,thumbs,percentages,likes,last_contacts,online",
        }
        search_parameters.update(self._parameters)
        return search_parameters

    def fetch(self, after=None, count=18):
        request_parameters = self._request_params(after=after, count=count)
        log.info(simplejson.dumps(request_parameters))
        response = self._session.okc_post(**request_parameters)
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
            ))
        else:
            for profile_info in profile_infos:
                yield Profile(self._session, profile_info["username"])


class GentationFilter(search_filters.filter_class):

    def transform(gentation):
        if isinstance(gentation, six.string_types):
            gentations = [gentation]
        else:
            gentations = gentation
        return [
            magicnumbers.gentation_to_number.get(
                a_gentation.strip().lower(), gentation
            )
            for a_gentation in gentations
        ]

    descriptions = "A list of the allowable gentations of returned search results."
    types = list
    acceptable_values = magicnumbers.gentation_to_number.keys()


class MinimumAgeFilter(search_filters.filter_class):

    keys = 'minimum_age'

    descriptions = "Filter profiles with ages above the provided value."
    types = int


class MaximumAgeFilter(search_filters.filter_class):

    keys = 'maximum_age'

    descriptions = "Filter profiles with ages below the provided value."
    types = int


class RadiusFilter(search_filters.filter_class):

    output_key = "radius"
    descriptions = "The maximum distance (in miles) from the specified location of returned search results."
    types = "int or None"

    def transform(radius):
        return radius


class LocationActivationFilter(search_filters.filter_class):

    output_key = "located_anywhere"
    types = (int, type(None))

    def transform(radius):
        return 1 if radius is None else 0


class LocIdFilter(search_filters.filter_class):

    types = int

    def transform(locid):
        return locid


class LocationFilter(search_filters.filter_class):

    output_key = "locid"
    descriptions = (
        "A query that will be used to look up a locid for the search, location_cache must also be passed in in order for this parameter to work. :class:`~okcupyd.user.User` automatically passes the location_cache in.",
        "A :class:`~okcupyd.location.LocationQueryCache` instance."
    )

    # TODO:
    # Requiring location_cache here is a weird type of dependency
    # injection. A better solution is probably needed long term
    def transform(location, location_cache):
        return location_cache.get_locid(location)


def search(session=None, count=1, **kwargs):
    return SearchFetchable(session, count=count, **kwargs)[:count]


class OrderByFilter(search_filters.filter_class):

    def transform(order_by):
        return order_by or "SPECIAL_BLEND"


search_filters.add_to_docstring_of(SearchFetchable)
