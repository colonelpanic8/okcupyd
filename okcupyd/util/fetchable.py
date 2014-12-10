"""
Most of the collection objects that are returned from function
invocations in the okcupyd library are instances of
:class:`~okcupyd.util.fetchable.Fetchable`. In most cases, it is fine
to treat these objects as though they are lists because they can be iterated
over, sliced and accessed by index, just like lists:

.. code:: python

   for question in user.profile.questions:
       print(question.answer.text)

   a_random_question = user.profile.questions[2]
   for question in questions[2:4]:
       print(question.answer_options[0])

However, in some cases, it is important to be aware of the subtle
differences between :class:`~okcupyd.util.fetchable.Fetchable` objects
and python lists.
:class:`~okcupyd.util.fetchable.Fetchable` construct the elements that
they "contain" lazily. In most of its uses in the okcupyd library,
this means that http requests can be made to populate
:class:`~okcupyd.util.fetchable.Fetchable` instances as its elments
are requested.

The :attr:`~okcupyd.profile.Profile.questions`
:class:`~okcupyd.util.fetchable.Fetchable` that is used in the example
above fetches the pages that are used to construct its contents in
batches of 10 questions. This means that the actual call to retrieve
data is made when iteration starts. If you enable the request logger
when you run this code snippet, you get output that illustrates this
fact:

.. code::

   2014-10-29 04:25:04 Livien-MacbookAir requests.packages.urllib3.connectionpool[82461] DEBUG "GET /profile/ShrewdDrew/questions?leanmode=1&low=11 HTTP/1.1" 200 None
    Yes
    Yes
    Kiss someone.
    Yes.
    Yes
    Sex.
    Both equally
    No, I wouldn't give it as a gift.
    Maybe, I want to know all the important stuff.
    Once or twice a week
    2014-10-29 04:25:04 Livien-MacbookAir requests.packages.urllib3.connectionpool[82461] DEBUG "GET /profile/ShrewdDrew/questions?leanmode=1&low=21 HTTP/1.1" 200 None
    No.
    No
    No
    Yes
    Rarely / never
    Always.
    Discovering your shared interests
    The sun
    Acceptable.
    No.

Some fetchables will continue fetching content for quite a long time.
The search fetchable, for example, will fetch content until okcupid runs
out of search results. As such, things like:

.. code:: python

    for profile in user.search():
        profile.message("hey!")

should be avoided, as they are likely to generate a massive number of requests
to okcupid.com.


Another subtlety of the :class:`~okcupyd.util.fetchable.Fetchable`
class is that its instances cache its contained results. This means that
the second iteration over :attr:`okcupyd.profile.Profile.questions` in the
example below does not result in any http requests:

.. code:: python

    for question in user.profile.questions:
        print(question.text)

    for question in user.profile.questions:
        print(question.answer)

It is important to understand that this means that the contents of a
:class:`~okcupyd.util.fetchable.Fetchable` are not guarenteed to be in
sync with okcupid.com the second time they are requested. Calling
:meth:`~okcupyd.util.fetchable.Fetchable.refresh` will cause the
:class:`~okcupyd.util.fetchable.Fetchable` to request new data from
okcupid.com when its contents are requested. The code snippet that
follows prints out all the questions that the logged in user has
answered roughly once per hour, including ones that are answered while
the program is running.


.. code:: python

    import time

    while True:
        for question in user.profile.questions:
            print(question.text)
        user.profile.questions.refresh()
        time.sleep(3600)

Without the call to  `user.profile.questions.refresh()`, this program
would never update the user.profile.questions instance, and thus what
would be printed to the screen with each iteration of the for loop.
"""
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
    """Applies object_factory to each element found with element_xpath

    Accepts session merely to be consistent with the FetchMarshall interface.
    """

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
