import operator

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
