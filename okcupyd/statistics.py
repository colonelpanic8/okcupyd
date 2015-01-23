import itertools
import numbers

from . import util
from .attractiveness_finder import AttractivenessFinder


class Statistics(object):

    def __init__(self, user, message_threads=None, filters=(),
                 attractiveness_finder=None):
        self._user = user
        self._message_threads = message_threads or set(itertools.chain(user.inbox,
                                                                       user.outbox))
        self._filters = filters
        self._attractiveness_finder = attractiveness_finder or AttractivenessFinder()

    def _thread_matches(self, message_thread):
        return all(f(message_thread) for f in self._filters)

    @util.cached_property
    def threads(self):
        return set(mt for mt in self._message_threads if self._thread_matches(mt))

    @util.cached_property
    def has_messages(self):
        return self.with_filters(lambda mt: mt.has_messages)

    @util.cached_property
    def has_response(self):
        return self.with_filters(lambda mt: mt.got_response)

    @util.cached_property
    def no_responses(self):
        return self.with_filters(lambda mt: not mt.got_response)

    @util.cached_property
    def initiated(self):
        return self.with_filters(lambda mt: mt.initiator == self._user.profile)

    @util.cached_property
    def received(self):
        return self.with_filters(lambda mt: mt.initiator != self._user.profile)

    @util.cached_property
    def has_attractiveness(self):
        return self.with_filters(lambda mt: self._attractiveness_finder.find_attractiveness(
            mt.correspondent) is not None)

    def time_filter(self, min_date=None, max_date=None):
        def _time_filter(thread):
            if min_date and min_date > thread.date:
                return False
            if max_date and max_date < thread.date:
                return False
            return True
        return self.with_filters(_time_filter)

    def attractiveness_filter(self, attractiveness_finder=None,
                                   min_attractiveness=0, max_attractiveness=10000):
        attractiveness_finder = attractiveness_finder or self._attractiveness_finder
        def _attractiveness_filter(thread):
            attractiveness = attractiveness_finder.find_attractiveness(
                thread.correspondent
            )
            return (isinstance(attractiveness, numbers.Number) and
                    min_attractiveness <= attractiveness <= max_attractiveness)
        return self.with_filters(_attractiveness_filter)

    def with_filters(self, *filters, **kwargs):
        message_threads = self.threads \
                          if kwargs.get('apply_filters_immediately', True) \
                          else self._message_threads
        return type(self)(self._user, message_threads, self._filters + filters,
                          attractiveness_finder=self._attractiveness_finder)

    @property
    def count(self):
        return len(self.threads)

    @property
    def response_rate(self):
        return float(self.has_response.count)/self.count

    def _average(self, function):
        return sum(map(function, self.threads))/self.count

    @property
    def average_first_message_length(self):
        return self._average(lambda thread: len(thread.messages[0].content))

    @property
    def average_conversation_length(self):
        return self._average(lambda thread: thread.message_count)

    def _average_attractiveness(self, attractiveness_finder=None):
        attractiveness_finder = attractiveness_finder or self._attractiveness_finder
        return self.has_attractiveness._average(lambda thread: (
            attractiveness_finder.find_attractiveness(
                thread.correspondent
            ))
        )

    @property
    def average_attractiveness(self):
        return self._average_attractiveness()

    @property
    def portion_initiated(self):
        return self.initiated.count/self.count

    @property
    def portion_received(self):
        return 1 - self.portion_initiated
