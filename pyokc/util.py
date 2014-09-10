import collections
import functools
import inspect


class n_partialable(object):

    @staticmethod
    def arity_evaluation_checker(function):
        function_info = inspect.getargspec(function)
        function_args = function_info.args
        if inspect.isclass(function):
            # This is to handle the fact that self will get passed in automatically.
            function_args = function_args[1:]
        def evaluation_checker(*args, **kwargs):
            acceptable_kwargs = function_args[len(args):]
            kwarg_keys = set(kwargs.keys())
            # Make sure that we didn't get an argument we can't handle.
            assert kwarg_keys.issubset(acceptable_kwargs)
            needed_args = function_args[len(args):]
            if function_info.defaults:
                needed_args = needed_args[:-len(function_info.defaults)]
            return not needed_args or kwarg_keys.issuperset(needed_args)
        return evaluation_checker

    def __init__(self, function, evaluation_checker=None, args=None, kwargs=None):
        self.function = function
        self.evaluation_checker = (evaluation_checker or
                                   self.arity_evaluation_checker(function))
        self.args = args or ()
        self.kwargs = kwargs or {}

    def __call__(self, *args, **kwargs):
        new_args = self.args + args
        new_kwargs = self.kwargs.copy()
        new_kwargs.update(kwargs)
        if self.evaluation_checker(*new_args, **new_kwargs):
            return self.function(*new_args, **new_kwargs)
        else:
            return type(self)(self.function, self.evaluation_checker,
                              new_args, new_kwargs)


n_partialable = n_partialable(n_partialable)


def makelist(value):
    if not isinstance(value, list):
        if isinstance(value, collections.Iterable):
            return list(value)
        else:
            return [value]
    return value


def makelist_decorator(function):
    @functools.wraps(function)
    def wrapped(arg):
        return function(makelist(arg))

    return wrapped


class cached_property(object):

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def attribute_contains_xpath_string(attribute, contained_string):
    return "contains(concat(' ',normalize-space(@{0}),' '),' {1} ')".format(
        attribute, contained_string
    )


def attribute_contains_xpath_strings(attribute, contained_strings, is_or=False):
    join_string = ' or ' if is_or else ' and '
    return join_string.join(attribute_contains_xpath_string(attribute, contained_string)
                        for contained_string in contained_strings)


def find_elements_with_classes_xpath(elem_type, elem_classes, is_or=False):
    return './/{0}[{1}]'.format(elem_type, attribute_contains_xpath_strings('class', elem_classes, is_or=is_or))


def find_elements_with_classes(tree, elem_type, elem_classes, is_or=False):
    return tree.xpath(find_elements_with_classes_xpath(elem_type, elem_classes, is_or=is_or))


class LazyReusableContainer(object):

    def __init__(self, fetcher):
        self._fetcher = fetcher
        self._fetched = []

    def __getitem__(self, item):
        if isinstance(item, slice):
            pass
        else:
            if item >= len(self._fetched):
                self._fetcher.fetch(item, self._fetched)
        return self._fetched[item]
