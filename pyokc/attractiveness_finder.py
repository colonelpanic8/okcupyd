from .objects import Session
from .search import search


class AttractivenessFinder(object):

    def __init__(self):
        self._session = Session.login()

    def find_attractiveness(self, username, accuracy=10, _lower=0, _higher=10000):
        average = (_higher + _lower)//2
        print('searching between {0} and {1}'.format(average, _higher))
        if _higher - _lower < accuracy:
            return average

        results = search(self._session,
                         looking_for='everybody',
                         keywords=username,
                         attractiveness_min=average,
                         attractivenvess_max=_higher)

        if results:
            print('found')
            return self.find_attractiveness(username, accuracy, average, _higher)
        else:
            print('not found')
            return self.find_attractiveness(username, accuracy, _lower, average)
