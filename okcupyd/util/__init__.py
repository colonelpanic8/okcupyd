import functools
import collections
import inspect

from .fetchable import Fetchable, FetchMarshall
from .compose import compose
from .currying import curry
from .misc import *

_pyflakes_ignore = (compose, curry, Fetchable, FetchMarshall)



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

