import itertools
import operator

import mock
import pytest
import six

from okcupyd import util


@util.curry
def crazy(a, self):
    return a + self.starter


class HasCurryMethods(object):

    def __init__(self, starter):
        self.starter = starter
        self.on_instance = crazy

    @util.curry
    def curry(self, x, y=0):
        return self.starter * x * y

    on_class = crazy(1)


def test_curry_method_behavior():
    assert HasCurryMethods(2).curry(y=2)(1) == 4
    hpm = HasCurryMethods(2)
    assert hpm.on_instance(2, hpm) == 4
    assert hpm.on_class() == 3


def test_curry_with_kwargs_taking_function():
    @util.curry
    def kwarg_taking_function(arg, **kwargs):
        kwargs['k'] = arg
        return kwargs

    assert kwarg_taking_function(a=14)(2) == {'k': 2, 'a': 14}


def test_curry_cache_behavior_problems():

    class CurryCacheTest(object):
        def func(self, a=1):
            return 2 + a

        test = util.curry(func)

        def func(self):
            return 1

    instance = CurryCacheTest()
    assert instance.func() == 1
    assert instance.test() == 3
    assert instance.func() == 1

    # Ensure we are getting new bound instances each time
    assert instance.test is not instance.test
    assert instance.func is not instance.func

    class CurryCacheTest2(object):
        def func(self, a=1):
            return 2 + a

        test = util.curry(func, cache_name='test')

        @util.curry(cache_name=True)
        def func(self):
            return 1

    instance = CurryCacheTest2()
    assert instance.func() == 1
    assert instance.test() == 3
    assert instance.func() == 1

    # Ensure we are caching the result of the curry each time
    assert instance.test is instance.test
    assert instance.func is instance.func


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

    @util.curry
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


def test_curry_on_classmethod():
    class TestClass(object):

        @classmethod
        @util.curry
        def test(cls, arg, optional=3):
            return optional + arg

    assert TestClass.test(optional=1)(2) == 3
    assert TestClass().test(optional=3)(2) == 5


def test_decorate_all():
    def add_two(function):
        def wrap(*args, **kwargs):
            return function(*args, **kwargs) + 2
        return wrap

    class Test(six.with_metaclass(util.decorate_all(add_two))):

        def one(self):
            return 1

        def two(self):
            return 2

    assert Test().one() == 3
    assert Test().two() == 4


def test_staticmethod_decorate_all():
    class Test(six.with_metaclass(util.decorate_all(staticmethod))):
        def test():
            return 1

        def test2(a, b):
            return a + b

    assert Test.test() == 1
    assert Test.test2(1, 1) == 2
