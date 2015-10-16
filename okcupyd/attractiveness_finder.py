from .json_search import search
from .session import Session
from . import settings
from . import util


class _AttractivenessFinder(object):
    """Find the attractiveness of okcupid.com users.

    This class is typically wrapped in several different attractiveness
    finder decorators that allow for cacheing of results and rounding.
    """

    def __init__(self, session=None):
        self._session = session or Session.login(settings.AF_USERNAME,
                                                 settings.AF_PASSWORD)

    def find_attractiveness(self, username, accuracy=1000,
                            _lower=0, _higher=10000):
        """
        :param username: The username to lookup attractiveness for.
        :param accuracy: The accuracy required to return a result.
        :param _lower: The lower bound of the search.
        :param _higher: The upper bound of the search.
        """
        average = (_higher + _lower)//2
        if _higher - _lower <= accuracy:
            return average

        results = search(self._session,
                         count=9,
                         gentation='everybody',
                         keywords=username,
                         attractiveness_min=average,
                         attractiveness_max=_higher,)
        found_match = False
        if results:
            for profile in results:
                if profile.username.lower() == username:
                    found_match = True
                    break

        if found_match:
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
                           gentation='everybody',
                           keywords=username,
                           count=1))


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
