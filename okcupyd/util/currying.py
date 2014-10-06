import inspect


class curry(object):

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

    def __repr__(self):
        return '<{0}.{1} of {2}>'.format(__name__, type(self).__name__, 
                                  repr(self.function))


curry = curry(curry)
