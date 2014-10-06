import logging

import simplejson

from . import helpers
from . import util
from .filter import Filters
from .profile import Profile
from .session import Session
from .xpath import xpb


log = logging.getLogger(__name__)


_username_xpb = xpb.div.with_classes('match_card').div.with_class('username').a.text_
def SearchFetchable(session=None, **kwargs):
    """Build a search object that conforms to the fetcher interface of
    :class:`.util.fetchable.Fetchable`.
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


class SearchHTMLFetcher(object):

    _username_xpb = xpb.div.with_class('username')

    def __init__(self, session=None, **options):
        self._session = session or Session.login()
        self._options = options
        self._filter_builder = Filters(**options)

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
        search_parameters.update(self._filter_builder.build())
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
