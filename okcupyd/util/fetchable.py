import itertools
from lxml import html


class Fetchable(object):
    """List-like container object that lazily loads its contained items."""

    @classmethod
    def fetch_marshall(cls, fetcher, processor):
        return cls(FetchMarshall(fetcher, processor))

    def __init__(self, fetcher, **kwargs):
        """
        :param fetcher: An object with a `fetch` generator method that retrieves
                        items for the fetchable.
        :param nice_repr: Append the repr of a list containing the items that
                          have been fetched to this point by the fetcher. Defaults
                          to True
        :param kwargs: Arguments that should be passed to the fetcher when it's
                       fetch method is called. These are stored on the fetchable
                       so they can be passed to the fetcher whenever
                       :meth:`refresh` is called.
        """
        self._fetcher = fetcher
        self._kwargs = kwargs
        self.refresh()

    def refresh(self, nice_repr=True, **kwargs):
        """
        :param nice_repr: Append the repr of a list containing the items that
                          have been fetched to this point by the fetcher.
        :type nice_repr: bool
        :param kwargs: kwargs that should be passed to the fetcher when its
                       fetch method is called. These are merged with the values
                       provided to the constructor, with the ones provided here
                       taking precedence if there is a conflict.
        """
        for key, value in self._kwargs.items():
            kwargs.setdefault(key, value)
        # No real good reason to hold on to this. DONT TOUCH.
        self._original_iterable = self._fetcher.fetch(**kwargs)
        self.exhausted = False
        if nice_repr:
            self._accumulated = []
            self._original_iterable = self._make_nice_repr_iterator(
                self._original_iterable, self._accumulated
            )
        else:
            self._accumulated = None
        self._clonable, = itertools.tee(self._original_iterable, 1)
        return self

    @staticmethod
    def _make_nice_repr_iterator(original_iterable, accumulator):
        for item in original_iterable:
            accumulator.append(item)
            yield item

    __call__ = refresh

    def __iter__(self):
        # This is hard to think about, but you can't ever use an iterator
        # if you plan on cloning it. Furthermore, you can only clone it once
        # (directly). For this reason, we throw away the iterator once it has
        # been cloned.
        new_iterable, self._clonable = itertools.tee(self._clonable, 2)
        return new_iterable

    def __getitem__(self, item):
        if not isinstance(item, slice):
            iterator = iter(self)
            assert isinstance(item, int)
            if item < 0:
                return list(iterator)[item]
            try:
                for i in range(item):
                    next(iterator)
                return next(iterator)
            except StopIteration:
                self.exhausted = True
                raise IndexError("The Fetchable does not have a value at the "
                                 "index that was provided.")
        return self._handle_slice(item)

    def _handle_slice(self, item):
        iterator = iter(self)
        if item.start is None and item.stop is None:
            # No point in being lazy if they want it all.
            self.exhausted = True
            return list(iterator)[item]
        if ((item.start and item.start < 0) or
            (not item.stop or item.stop < 0)):
            # If we have any negative numbers we have to expand the whole
            # thing anyway. This is also the case if there is no bound
            # on the slice, hence the `not item.stop` trigger.
            self.exausted = True
            return list(iterator)[item]
        accumulator = []
        # No need to do this for stop since we are sure it is not None.
        start = item.start or 0
        for _ in range(start):
            try:
                next(iterator)
            except StopIteration: # This is strange but its what list do.
                self.exhausted = True
                break
        for i in range(item.stop - start):
            try:
                value = next(iterator)
            except StopIteration:
                self.exhausted = True
                break
            else:
                if item.step == None or i % item.step == 0:
                    accumulator.append(value)
        return accumulator

    def __repr__(self):
        fetched_type = repr(self._fetcher)
        if self._accumulated == None:
            list_repr = ''
        else:
            try:
                self[0]
            except:
                pass
            else:
                fetched_type = type(self._accumulated[0]).__name__
            list_repr = repr(self._accumulated)
            if not self.exhausted:
                if len(self._accumulated) == 0:
                    list_repr = '[...]'
                else:
                    list_repr = '{0}, ...]'.format(list_repr[:-1])

        return '<{0}[{1}]{2}>'.format(type(self).__name__,
                                    fetched_type, list_repr)

    def __len__(self):
        return len(self[:])

    def __add__(self, other):
        return self[:] + other[:]

    def __eq__(self, other):
        return self[:] == other[:]

    def __nonzero__(self):
        try:
            self[0]
        except IndexError:
            return False
        else:
            return True


class FetchMarshall(object):

    def __init__(self, fetcher, processor, terminator=None, start_at=1):
        self._fetcher = fetcher
        self._start_at = start_at
        self._processor = processor
        self._terminator = terminator or self.simple_decider

    @staticmethod
    def simple_decider(pos, last, text_response):
        return pos > last

    def fetch(self, start_at=None):
        pos = start_at or self._start_at
        while True:
            last = pos
            text_response = self._fetcher.fetch(start_at=pos)
            if not text_response: break
            for item in self._processor.process(text_response):
                if item is StopIteration:
                    raise StopIteration()
                yield item
                pos += 1
            if not self._terminator(pos, last, text_response):
                break

    def __repr__(self):
        return '{0}({1}, {2})'.format(type(self).__name__,
                                      repr(self._fetcher),
                                      repr(self._processor))


class SimpleProcessor(object):

    def __init__(self, session, object_factory, element_xpath):
        self._object_factory = object_factory
        self._element_xpath = element_xpath

    def process(self, text_response):
        if not text_response.strip():
            yield StopIteration
            raise StopIteration()
        for element in self._element_xpath.apply_(
            html.fromstring(text_response)
        ):
            yield self._object_factory(element)

    def __repr__(self):
        return '<{0}({1}, {2})>'.format(type(self).__name__,
                                        repr(self._object_factory),
                                        repr(self._element_xpath))


class PaginationProcessor(object):

    def __init__(self, object_factory, element_xpb,
                 current_page_xpb, total_page_xpb):
        self._object_factory = object_factory
        self._element_xpb = element_xpb
        self._current_page_xpb = current_page_xpb
        self._total_page_xpb = total_page_xpb

    def _current_page(self, tree):
        return int(self._current_page_xpb.one_(tree))

    def _page_count(self, tree):
        return int(self._total_page_xpb.one_(tree))

    def _are_pages_left(self, tree):
        return self._current_page(tree) < self._page_count(tree)

    def process(self, text_response):
        tree = html.fromstring(text_response)
        for element in self._element_xpb.apply_(tree):
            yield self._object_factory(element)
        if not self._are_pages_left(tree):
            # This is pretty gross: Part of the processor protocol
            # is that if StopIteration is yielded, the loop above
            # will be terminated. No easy way around this short
            # of making bigger objects or abstracting less.
            yield StopIteration


class GETFetcher(object):

    def __init__(self, session, path, query_param_builder=lambda: {}):
        self._session = session
        self._path = path
        self._query_param_builder = query_param_builder

    def fetch(self, *args, **kwargs):
        response = self._session.okc_get(
            self._path, params=self._query_param_builder(*args, **kwargs)
        )
        return response.content.strip()

    def __repr__(self):
        return '<{0}("{1}")>'.format(type(self).__name__, self._path)
