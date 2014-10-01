import collections
import functools
import getpass
import inspect
import importlib
import itertools
import logging
import shutil
import sys

from coloredlogs import ColoredStreamHandler

from . import settings


BASE_URI = 'https://www.okcupid.com/'


class n_partialable(object):

    @staticmethod
    def arity_evaluation_checker(function):
        is_class = inspect.isclass(function)
        if is_class:
            function = function.__init__
        function_info = inspect.getargspec(function)
        function_args = function_info.args
        if is_class:
            # This is to handle the fact that self will get passed in
            # automatically.
            function_args = function_args[1:]
        def evaluation_checker(*args, **kwargs):
            kwarg_keys = set(kwargs.keys())
            if function_info.keywords == None:
                acceptable_kwargs = function_args[len(args):]
                # Make sure that we didn't get an argument we can't handle.
                try:
                    assert kwarg_keys.issubset(acceptable_kwargs)
                except:
                    import ipdb; ipdb.set_trace()
            needed_args = function_args[len(args):]
            if function_info.defaults:
                needed_args = needed_args[:-len(function_info.defaults)]
            return not needed_args or kwarg_keys.issuperset(needed_args)
        return evaluation_checker

    @staticmethod
    def count_evaluation_checker(count):
        def function(*args, **kwargs):
            return len(args) >= count
        return function

    def __init__(self, function, evaluation_checker=None, args=(), kwargs=None):
        self.function = function
        self.evaluation_checker = (evaluation_checker or
                                   self.arity_evaluation_checker(function))
        self.args = args
        self.kwargs = kwargs or {}
        self.__name__ = function.__name__

    def __call__(self, *args, **kwargs):
        new_args = self.args + args
        new_kwargs = self.kwargs.copy()
        new_kwargs.update(kwargs)
        if self.evaluation_checker(*new_args, **new_kwargs):
            return self.function(*new_args, **new_kwargs)
        else:
            return type(self)(self.function, self.evaluation_checker,
                              new_args, new_kwargs)

    def __get__(self, obj, obj_type):
        bound = type(self)(self.function, self.evaluation_checker,
                           args=self.args + (obj,), kwargs=self.kwargs)
        setattr(obj, self.function.__name__, bound)
        return bound


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


def _compose2(f, g):
    return lambda *args, **kwargs: f(g(*args, **kwargs))


@n_partialable(evaluation_checker=n_partialable.count_evaluation_checker(2))
def compose_with_joiner(joiner, *functions):
    return functools.reduce(joiner, functions)


compose_one_arg = compose_with_joiner(_compose2)


compose = compose_with_joiner(lambda f, g: _compose2(make_single_arity(f),
                                                force_args_return(g)))

def make_single_arity(function):
    @functools.wraps(function)
    def wrapped(args):
        return function(*args)
    return wrapped


def force_args_return(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        value = function(*args, **kwargs)
        if not isinstance(value, collections.Iterable):
            value = (value,)
        return value
    return wrapped


def tee(*functions):
    def wrapped(*args, **kwargs):
        return tuple(function(*args, **kwargs) for function in functions)
    return wrapped


def enable_logger(log_name, level=logging.DEBUG):
    log = logging.getLogger(log_name)
    handler = ColoredStreamHandler()
    handler.setLevel(level)
    log.setLevel(level)
    log.addHandler(handler)


def get_credentials():
    if not settings.USERNAME:
        input_function = input if sys.version_info.major == 3 else raw_input
        settings.USERNAME = input_function('username: ').strip()
    if not settings.PASSWORD:
        settings.PASSWORD = getpass.getpass('password: ')


def add_command_line_options(add_argument, use_short_options=True):
    logger_args = ("--enable-logger",)
    credentials_args = ("--credentials",)
    if use_short_options:
        logger_args += ('-l',)
        credentials_args += ('-c',)
    add_argument(*logger_args, dest='enabled_loggers',
                 action="append", default=[],
                 help="Enable the specified logger.")
    add_argument(*credentials_args, dest='credentials_modules',
                 action="append", default=[],
                 help="Use the specified credentials module to update "
                 "the values in okcupyd.settings.")
    add_argument('--echo', dest='echo', action='store_true', default=False,
                 help="Echo SQL.")


def handle_command_line_options(args):
    for enabled_log in args.enabled_loggers:
        enable_logger(enabled_log)
    for credentials_module in args.credentials_modules:
        update_settings_with_module(credentials_module)
    if args.echo:
        from okcupyd import db
        db.echo = True
        db.Session.kw['bind'].echo = True
    return args


def update_settings_with_module(module_name):
    module = importlib.import_module(module_name)
    if hasattr(module, 'USERNAME') and module.USERNAME:
        settings.USERNAME = module.USERNAME
    if hasattr(module, 'PASSWORD') and module.PASSWORD:
        settings.PASSWORD = module.PASSWORD
    if hasattr(module, 'AF_USERNAME') and module.AF_USERNAME:
        settings.AF_USERNAME = module.AF_USERNAME
    if hasattr(module, 'AF_PASSWORD') and module.AF_PASSWORD:
        settings.AF_PASSWORD = module.AF_PASSWORD


def save_file(filename, data):
    with open(filename, 'wb') as out_file:
        shutil.copyfileobj(data, out_file)


class Fetchable(object):

    def __init__(self, fetcher, **kwargs):
        self._fetcher = fetcher
        self._kwargs = kwargs
        self.refresh()

    def refresh(self, nice_repr=True, **kwargs):
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
        iterator = iter(self)

        if not isinstance(item, slice):
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

        # We have a slice
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
        if self._accumulated == None:
            list_repr = ''
        else:
            list_repr = repr(self._accumulated)
            if not self.exhausted:
                if len(self._accumulated) == 0:
                    list_repr = '[...]'
                else:
                    list_repr = '{0}, ...]'.format(list_repr[:-1])
        return '{0}({1}){2}'.format(type(self).__name__,
                                    repr(self._fetcher), list_repr)

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

    STOP = object()

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


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


def replace_all_case_insensitive(a_str, sub, replacement):
    segments = []
    last_stop = 0
    for start in find_all(a_str.lower(), sub.lower()):
        segments.append(a_str[last_stop:start])
        segments.append(replacement)
        last_stop = start + len(sub)
    segments.append(a_str[last_stop:])
    return ''.join(segments)
