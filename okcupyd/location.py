from .session import Session


class NoLocationFoundError(Exception):
    pass


class LocationQueryCache(object):

    def __init__(self, session=None):
        self._session = session or Session.login()
        self._locid_cache = {}
        self._query_cache = {}

    def get_locid(self, query):
        if query in self._query_cache:
            return self._query_cache[query]
        result = self._query(query)
        if 'results' in result and len(result['results']):
            locid = result['results'][0]['locid']
            if locid not in self._locid_cache:
                self._locid_cache[locid] = result['results'][0]
            return locid
        raise NoLocationFoundError()

    def get(self, query):
        locid = self.get_locid(query)
        if locid:
            return self._locid_cache[locid]

    def _query(self, query):
        return self._session.okc_get(
            'apitun/location/query',
            params={'q': query, 'access_token': self._session.access_token},
        ).json()
