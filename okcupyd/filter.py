import inspect

from . import util
from . import magicnumbers


class Filters(object):
    """Registrar for functions that construct filters for submission in
    requests to okcupid.com
    """

    def __init__(self):
        self.builder_to_keys = {}
        self.builder_to_decider = {}
        self.keys = set()
        self._key_to_type = {}
        self._key_to_values = {}
        self._key_to_string = {}

    def build_documentation_lines(self):
        """Build a parameter documentation string that can appended to the
        docstring of a function that uses this :class:`~.Filters` instance
        to build filters.
        """
        return [
            line_string for key in sorted(self.keys)
            for line_string in self.build_paramter_string(key)
        ]

    def build_paramter_string(self, key):
        description_string = u''
        if key in self._key_to_string:
            description_string = u' {0}'.format(self._key_to_string[key])
        if key in self._key_to_values:
            description_string += u' expected values: {0}'.format(
                u', '.join([repr(value)
                           for value in self._key_to_values[key]])
            )
        parameter_string_lines = [u':param {0}:{1}'.format(
            key, description_string
        )]
        if key in self._key_to_type:
            the_type = self._key_to_type[key]
            parameter_string_lines.append(u':type {0}: {1}'.format(
                key, the_type.__name__ if isinstance(the_type, type) else the_type
            ))
        return parameter_string_lines

    @staticmethod
    def any_decider(function, incoming, accepted_keys):
        return bool(set(incoming).intersection(accepted_keys))

    @staticmethod
    def all_decider(function, incoming, accepted_keys):
        return set(accepted_keys).issubset(set(incoming))

    @staticmethod
    def all_not_none_decider(function, incoming, accepted_keys):
        return all(incoming.get(key) is not None for key in accepted_keys)

    @staticmethod
    def any_not_none_decider(function, incoming, accepted_keys):
        return any(incoming.get(key) is not None for key in accepted_keys)

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__,
                                 repr(self.builder_to_keys.keys()))

    def filters(self, **kwargs):
        builders = [builder
                    for builder, decider in self.builder_to_decider.items()
                    if decider(builder, kwargs, self.builder_to_keys[builder])]
        return [builder(*[kwargs.get(key)
                          for key in self.builder_to_keys[builder]])
                for builder in builders]

    def build(self, **kwargs):
        if not self.keys.issuperset(kwargs.keys()):
            raise TypeError("build() got unexpected keyword arguments: "
                            "{0}".format(', '.join(
                                repr(k) for k in kwargs.keys()
                                if k not in self.keys
                            )))
        return {
            u'filter{0}'.format(filter_number): filter_string
            for filter_number, filter_string
            in enumerate(self.filters(**kwargs), 1)
        }

    @util.curry
    def register_filter_builder(self, function, keys=(), decider=None,
                                acceptable_values=None,
                                types=None,
                                descriptions=None):
        """Register a filter function with this :class:`~.Filters` instance.
        This function is curried with :class:`~okcupyd.util.currying.curry`
        -- that is, it can be invoked partially before it is fully evaluated.
        This allows us to pass kwargs to this function when it is used as a
        decorator:

        .. code-block:: python

            @register_filter_builder(keys=('real_name',),
                                     decider=Filters.any_decider)
            def my_filter_function(argument):
                return '4,{0}'.format(argument)

        :param function: The filter function to register.
        :param keys: Keys that should be used as the argument names for
                     `function`, if none are provided, the filter functions
                     argument names will be used instead.
        :param decider: a function of signature
                        `(function, incoming_keys, accepted_keys)` that returns
                        True if the filter function should be called and False
                        otherwise. Defaults to
                        :meth:`~.all_not_none_decider`
        :param acceptable_values: A list of acceptable values for the parameter
                                  of the filter function (or a list of lists if
                                  the filter function takes multiple parameters)
        :param types: The type of the parameter accepted by the incoming filter
                      function (or a list of types if the function takes
                      multiple parameters)
        :param descriptions: A description for the incoming filter function's
                             argument (or a list of descriptions if the filter
                             function takes multiple arguments)
        """
        decider = decider or self.all_not_none_decider
        function_arguments = inspect.getargspec(function).args
        if keys:
            assert len(keys) == len(function_arguments)
        else:
            keys = function_arguments
        self.builder_to_keys[function] = keys
        self.builder_to_decider[function] = decider

        self.keys.update(keys)
        self._update_docs_dict(self._key_to_type, types, keys)
        self._update_docs_dict(self._key_to_string, descriptions, keys)
        self._update_docs_dict(self._key_to_values, acceptable_values, keys)

        return function

    def _update_docs_dict(self, docs_dict, incoming, keys):
        if incoming:
            if not isinstance(incoming, dict):
                if len(keys) > 1:
                    assert len(keys) == len(incoming), (
                        "Got {0}, for keys: {1}".format(incoming, keys)
                    )
                    incoming = zip(keys, incoming)
                else:
                    incoming = {key: incoming for key in keys}
            docs_dict.update(incoming)


def gentation_filter(gentation):
    return u'0,{0}'.format(
        magicnumbers.gentation_to_number[gentation.strip().lower()]
    )


def age_filter(age_min=18, age_max=99):
    if age_min == None:
        age_min = 18
    return u'2,{0},{1}'.format(age_min, age_max)


def location_filter(radius):
    return u'3,{0}'.format(radius)
