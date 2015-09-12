import inspect


class curry(object):
    """Curry a function or method.

    Applying :class:`~okcupyd.util.currying.curry` to a function
    creates a callable with the same functionality that can be invoked
    with an incomplete argument list to create a partial application
    of the original function.

    .. code-block:: python

        @curry
        def greater_than(x, y):
           return x > y

        >>> less_than_40 = greater_than(40)
        >>> less_than_40(39)
        True
        >>> less_than_40(50)
        False

    :class:`~okcupyd.util.currying.curry` allows functions to be partially
    invoked an arbitary number of times:

    .. code-block:: python

        @curry
        def add_5_things(a, b, c, d, e):
            return a + b + c + d + e

        # All of the following invocations of add_5_things
        >>> add_5_things(1)(1)(1)(1)(1)
        5

        one_left = add_5_things(1, 1)(3)(4) # A one place function that will
        # add 1 + 1 + 3 + 4 = 9 to whatever is provided as its argument.

        >>>> one_left(5)
        14
        >>> one_left(6)
        15

    A particular compelling use case for :class:`~okcupyd.util.currying.curry`
    is the creation of decorators that take optional arguments:

    .. code-block:: python

        @curry
        def add_n(function, n=1):
            def wrapped(*args, **kwargs):
                return function(*args, **kwargs) + n
            return wrapped

        @add_n(n=12)
        def multiply_plus_twelve(x, y):
            return x * y

        @add_n
        def multiply_plus_one(x, y):
            return x * y

        >>> multiply_plus_one(1, 1)
        2
        >>> multiply_plus_twelve(1, 1)
        13

    Notice that we were able to apply `add_n` regardless of whether or not an
    optional argument had been supplied earlier.

    The version of curry that is available for import has been curried itself.
    That is, its constructor can be invoked partially:

    .. code-block:: python

        @curry(evaluation_checker=lambda *args, **kwargs: len(args) > 2)
        def args_taking_function(*args):
            return reduce(lambda x, y: x*y, args)

        >>> args_taking_function(1, 2)
        2
        >>> args_taking_function(2)(3)
        6
        >>> args_taking_function(2, 2, 2, 2)
        16
    """

    @staticmethod
    def arity_evaluation_checker(function):
        """Build an evaluation checker that will return True when it is
        guaranteed that all positional arguments have been accounted for.
        """
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
            if function_info.keywords is None:
                acceptable_kwargs = function_args[len(args):]
                # Make sure that we didn't get an argument we can't handle.
                if not kwarg_keys.issubset(acceptable_kwargs):
                    TypeError("Unrecognized Arguments: {0}".format(
                        [key for key in kwarg_keys
                         if key not in acceptable_kwargs]
                    ))

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

    def __init__(self, function, evaluation_checker=None,
                 args=(), kwargs=None, cache_name=False):
        """
        :param function: The function to curry.
        :evaluation checker: A function that controls when the function will
                             be evaluated. The evaluation checker recieves the
                             arguments that will be passed to the function when
                             making this decision.
        """
        self.function = function
        self.evaluation_checker = (evaluation_checker or
                                   self.arity_evaluation_checker(function))
        if cache_name is True:
            cache_name = self.function.__name__
        self.cache_name = cache_name
        self.args = args
        self.kwargs = kwargs or {}
        self.__name__ = function.__name__
        self.__doc__ = function.__doc__

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
        if obj is None:
            return self
        bound = type(self)(self.function, self.evaluation_checker,
                           args=self.args + (obj,), kwargs=self.kwargs)
        # This caches the new partial application of the function on the
        # instance. Its not clear that this is a good idea but I'm leaving
        # it for now.
        if self.cache_name:
            setattr(obj, self.cache_name, bound)
        return bound

    def __repr__(self):
        return '<{0}.{1} of {2}>'.format(__name__, type(self).__name__,
                                         repr(self.function))


curry = curry(curry)
