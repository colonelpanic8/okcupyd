import collections
import functools
import inspect
import logging
import re

import six

from .fetchable import *
from .compose import compose
from .currying import curry
from .misc import *

_pyflakes_ignore = (compose, curry, Fetchable, FetchMarshall,
                    GETFetcher, PaginationProcessor)
log = logging.getLogger(__name__)



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
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
        return value

    def bust_self(self, obj):
        if self.func.__name__ in obj.__dict__:
            delattr(obj, self.func.__name__)

    @classmethod
    def bust_caches(cls, obj):
        for name, _ in cls.get_cached_properties(obj):
            if name in obj.__dict__:
                delattr(obj, name)

    @classmethod
    def get_cached_properties(cls, obj):
        return inspect.getmembers(type(obj), lambda x: isinstance(x, cls))


class CallableMap(object):

    def __init__(self, func_value_pairs=()):
        if isinstance(func_value_pairs, dict):
            func_value_pairs = func_value_pairs.items()
        self.func_value_pairs = list(func_value_pairs)

    def __getitem__(self, item):
        for func, value in self.func_value_pairs:
            if func(item):
                return value
        raise KeyError('{0} did not match any of this objects functions.'.format(item))

    def __setitem__(self, function, value):
        self.add(func, value)

    def add(func, value):
        self.func_value_pairs.append((func, value))


class REMap(object):

    NO_DEFAULT = object()

    @classmethod
    def from_string_pairs(cls, string_value_pairs, **kwargs):
        return cls(re_value_pairs=[(re.compile(s), v)
                                   for s, v in string_value_pairs],
                   **kwargs)

    def __init__(self, re_value_pairs=(), default=NO_DEFAULT):
        self.default = default
        if isinstance(re_value_pairs, dict):
            re_value_pairs = re_value_pairs.items()
        self.re_value_pairs = list(re_value_pairs)

    def __getitem__(self, item):
        if item is None:
            if self.default is self.NO_DEFAULT:
                raise KeyError("None does not match any expression")
            else:
                return self.default
        for matcher, value in self.re_value_pairs:
            if matcher.search(item):
                return value
        if self.default is not self.NO_DEFAULT:
            if item is not None and len(item) > 1:
                log.warning("Returning default from REMAP for {0}.".format(
                    repr(item)
                ))
            return self.default
        else:
            raise KeyError('{0} did not match any of this objects regular'
                           'expressions.'.format(repr(item)))

    def __setitem__(self, re, value):
        self.add(re, value)

    def add(re, value):
        self.re_value_pairs.append((re, value))

    @property
    def pattern_to_value(self):
        return {expression.pattern: value
                for expression, value in self.re_value_pairs}


class GetAttrGetItem(type):

    def __getitem__(self, item):
        return getattr(self, item)


def IndexedREMap(*re_strings, **kwargs):
    default = kwargs.get('default', 0)
    offset = kwargs.get('offset', 1)
    string_index_pairs = []
    for index, string_or_tuple in enumerate(re_strings, offset):
        if isinstance(string_or_tuple, six.string_types):
            string_or_tuple = (string_or_tuple,)
        for re_string in string_or_tuple:
            string_index_pairs.append((re_string, index))
    remap = REMap.from_string_pairs(string_index_pairs,
                                    default=default)
    return remap


