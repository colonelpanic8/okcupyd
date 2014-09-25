from .search import search
from .session import Session
from . import settings
from . import util


class _AttractivenessFinder(object):

    def __init__(self, session=None):
        self._session = session or Session.login(settings.AF_USERNAME,
                                                 settings.AF_PASSWORD)

    def find_attractiveness(self, username, accuracy=900,
                            _lower=0, _higher=10000):
        average = (_higher + _lower)//2
        if _higher - _lower <= accuracy:
            return average

        results = search(self._session,
                         looking_for='everybody',
                         keywords=username,
                         attractiveness_min=average,
                         attractiveness_max=_higher)

        if results:
            return self.find_attractiveness(username, accuracy,
                                            average, _higher)
        else:
            return self.find_attractiveness(username, accuracy,
                                            _lower, average)

    __call__ = find_attractiveness


class AttractivenessFinderDecorator(object):

    def __init__(self, attractiveness_finder=None):
        self._finder = attractiveness_finder or _AttractivenessFinder()

    def __getattr__(self, attr):
        return getattr(self._finder, attr)

    def __call__(self, *args, **kwargs):
        return self.find_attractiveness(*args, **kwargs)


class CheckForExistenceAttractivenessFinder(AttractivenessFinderDecorator):

    def _check_for_existence(self, username):
        return bool(search(self._session,
                           looking_for='everybody',
                           keywords=username))


    def find_attractiveness(self, username, *args, **kwargs):
        if self._check_for_existence(username):
            return self._finder(username, *args, **kwargs)


class RoundedAttractivenessFinder(AttractivenessFinderDecorator):

    def find_attractiveness(self, *args, **kwargs):
        unrounded = self._finder.find_attractiveness(*args, **kwargs)
        if unrounded is not None:
            return int(round(float(unrounded)/1000, 0)*1000)


class CachedAttractivenessFinder(AttractivenessFinderDecorator):

    def __init__(self, attractiveness_finder=None):
        self._finder = attractiveness_finder or _AttractivenessFinder()
        self._cache = {}

    def find_attractiveness(self, username, **kwargs):
        if username not in self._cache:
            self._cache[username] = self._finder(username, **kwargs)
        return self._cache[username]


AttractivenessFinder = util.compose(CachedAttractivenessFinder,
                                    RoundedAttractivenessFinder,
                                    CheckForExistenceAttractivenessFinder,
                                    _AttractivenessFinder)
