import itertools
import operator

import mock
import pytest

from okcupyd import util


@util.n_partialable
def crazy(a, self):
    return a + self.starter


class HasPartialableMethods(object):

    def __init__(self, starter):
        self.starter = starter
        self.on_instance = crazy

    @util.n_partialable
    def partialable(self, x, y=0):
        return self.starter * x * y

    on_class = crazy(1)


def test_partialable_method_behavior():
    assert HasPartialableMethods(2).partialable(y=2)(1) == 4
    hpm = HasPartialableMethods(2)
    assert hpm.on_instance(2, hpm) == 4
    assert hpm.on_class() == 3


def test_partialable_with_kwargs_taking_function():
    @util.n_partialable
    def kwarg_taking_function(arg, **kwargs):
        kwargs['k'] = arg
        return kwargs

    assert kwarg_taking_function(a=14)(2) == {'k': 2, 'a': 14}


def test_get_cached_properties():
    class PropClass(object):
        def __init__(self):
            self.count = 0

        @util.cached_property
        def count_prop(self):
            self.count += 1
            return self.count

        @util.cached_property
        def other_prop(self):
            return 4

    instance = PropClass()
    assert ['count_prop', 'other_prop'] == \
        list(map(operator.itemgetter(0),
                 util.cached_property.get_cached_properties(instance)))

    assert instance.count_prop == 1

    util.cached_property.bust_caches(instance)

    assert instance.count_prop == 2


def test_overwrite_kwarg():

    @util.n_partialable
    def test(k, a=0, b=0):
        return k + a + b

    assert test(a=4)(a=1)(1) == 2


def test_fetchable_teeing():
    fetcher = mock.Mock(fetch=lambda: itertools.count(5))
    fetchable = util.Fetchable(fetcher)
    first = iter(fetchable)
    second = iter(fetchable)

    assert next(first) == 5
    assert next(second) == 5

    third = iter(fetchable)

    assert next(third) == 5
    assert next(third) == 6
    assert next(third) == 7

    assert next(first) == 6
    assert next(second) == 6

    for i in range(4):
        assert next(iter(fetchable)) == 5

def test_fetchable_get_item():
    call_counter = mock.Mock()
    def fetch():
        for i in range(3):
            for i in range(5):
                yield i
            call_counter()
    fetcher = mock.Mock(fetch=fetch)
    fetchable = util.Fetchable(fetcher)

    assert fetchable[:2] == [0, 1]
    assert fetchable[:3] == [0, 1, 2]
    assert fetchable[3] == 3
    assert call_counter.call_count == 0

    assert fetchable[9] == 4
    assert call_counter.call_count == 1

    assert fetchable[2:3] == [2]

    assert fetchable[:] == fetchable[:]
    assert len(fetchable[:]) == 15

    # Go too far on purpose
    assert fetchable[:100000] == fetchable[:]

    # Go too far on purpose
    assert fetchable[100000:] == []
    assert fetchable[100000:10000000] == []

    with pytest.raises(IndexError):
        fetchable[12312312]


def test_negative_indexing():
    def fetch():
        yield 0
        yield 0
        yield 1
    fetcher = mock.Mock(fetch=fetch)
    fetchable = util.Fetchable(fetcher)
    assert fetchable[-1] == 1
    assert fetchable[-2:] == [0, 1]
    assert fetchable[14:] == []


def test_bool_on_fetchable():
    fetcher = mock.Mock(fetch=lambda: (i for i in range(0)))
    fetchable = util.Fetchable(fetcher)
    assert not fetchable

    fetcher = mock.Mock(fetch=lambda: (i for i in range(1)))
    fetchable = util.Fetchable(fetcher)

    assert fetchable

