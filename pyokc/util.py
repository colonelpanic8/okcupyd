import collections
import functools
import getpass
import importlib
import inspect
import logging

from . import settings


class n_partialable(object):

    @staticmethod
    def arity_evaluation_checker(function):
        function_info = inspect.getargspec(function)
        function_args = function_info.args
        if inspect.isclass(function):
            # This is to handle the fact that self will get passed in automatically.
            function_args = function_args[1:]
        def evaluation_checker(*args, **kwargs):
            kwarg_keys = set(kwargs.keys())
            if function_info.keywords == None:
                acceptable_kwargs = function_args[len(args):]
                # Make sure that we didn't get an argument we can't handle.
                assert kwarg_keys.issubset(acceptable_kwargs)
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


def kwargs_make_single_arity(function):
    @functools.wraps(function)
    def wrapped(kwargs):
        return function(**kwargs)
    return wrapped


def args_kwargs_make_single_arity(function):
    @functools.wraps(function)
    def wrapped(val):
        (args, kwargs) = val
        return function(*args, **kwargs)
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
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(name)s  %(asctime)s] %(message)s'))
    handler.setLevel(level)
    log.setLevel(level)
    log.addHandler(handler)


def get_credentials():
    if not settings.USERNAME:
        settings.USERNAME = input('username: ')
    if not settings.PASSWORD:
        settings.PASSWORD = getpass.getpass('password: ')


def add_command_line_options(add_argument, use_short_options=True):
    args = ("--enable-logger",)
    if use_short_options:
        args += ('-l',)
    add_argument(*args, dest='enabled_loggers',
                 action="append", default=[], help="Enable the specified log.")
    args = ("--credentials",)
    if use_short_options:
        args += ('-c',)
    add_argument(*args, dest='credentials_modules',
                 action="append", default=[],
                 help="Use the specified credentials module to update "
                 "the values in pyokc.settings.")


def handle_command_line_options(args):
    for enabled_log in args.enabled_loggers:
        enable_logger(enabled_log)
    for credentials_module in args.credentials_modules:
        update_settings_with_module(credentials_module)


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
