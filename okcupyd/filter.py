import inspect
import itertools

import six

from . import util
from . import magicnumbers


def all_not_none_decider(transform_funct, incoming_kwargs, accepted_keys):
    return all(incoming_kwargs.get(key) is not None for key in accepted_keys)

class Filters(object):
    """Registrar for functions that construct filters for submission in
    requests to okcupid.com
    """

    def __init__(self):
        self.builders = []
        self.keys = set()
        self._key_to_string = {}
        self._key_to_values = {}
        self._key_to_type = {}

    @util.cached_property
    def filter_meta(filters_instance):
        class FilterMeta(util.decorate_all(staticmethod)):

            output_key = None
            #: A container specifying the input keys, defaults to arguments of `transform`
            keys = ()
            #: One or more strings, same as the number of keys
            descriptions = None
            #: One or more iterables, same as the number of keys; docstring will use repr of the elements
            acceptable_values = None
            #: One or more types or strings, same as the number of keys
            types = None

            def __init__(cls, name, bases, attributes_dict):
                super(FilterMeta, cls).__init__(name, bases, attributes_dict)
                cls._set_defaults()
                filters_instance.register_builder(cls)

            # TODO: why not just decide = all_not_none_decider
            def decide(cls, kwargs):
                return all_not_none_decider(cls.transform, kwargs, cls.keys)

            def transform_from_kwargs(cls, kwargs):
                return cls.transform(*[kwargs.get(key) for key in cls.keys])

            def _set_defaults(cls):
                function_arguments = inspect.getargspec(cls.transform).args
                if cls.keys:
                    assert len(cls.keys) == len(function_arguments)
                else:
                    cls.keys = function_arguments

                if not cls.output_key:
                    # assert len(cls.keys) == 1
                    # cls.output_key, = cls.keys
                    cls.output_key = cls.keys[0]
        return FilterMeta

    @util.cached_property
    def filter_class(self):
        return six.with_metaclass(self.filter_meta)

    def build_documentation_lines(self):
        """Build a parameter documentation string that can appended to the
        docstring of a function that uses this :class:`~.Filters` instance
        to build filters.
        """
        return [
            line_string for key in sorted(self.keys)
            for line_string in self.build_parameter_string(key)
        ]

    def build_parameter_string(self, key):
        description_string = u''
        if key in self._key_to_string:
            description_string = u' {0}'.format(self._key_to_string[key])
        if key in self._key_to_values:
            description_string += u' Expected values: {0}'.format(
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

    def add_to_docstring_of(self, target):
        target.__doc__ = '\n    '.join(
            itertools.chain(
                (target.__doc__,), self.build_documentation_lines()
            )
        )

    all_not_none_decider = staticmethod(all_not_none_decider)

    @staticmethod
    def any_decider(transform_funct, incoming_kwargs, accepted_keys):
        return bool(set(incoming_kwargs).intersection(accepted_keys))

    @staticmethod
    def all_decider(transform_funct, incoming_kwargs, accepted_keys):
        return set(accepted_keys).issubset(set(incoming_kwargs))

    @staticmethod
    def any_not_none_decider(transform_funct, incoming_kwargs, accepted_keys):
        return any(incoming_kwargs.get(key) is not None for key in accepted_keys)

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__,
                                 repr(self.builder_to_keys.keys()))

    def filters(self, **kwargs):
        builders = [
            builder for builder in self.builders if self._handle_decide(builder, kwargs)
        ]
        return [
            builder.transform(
                *[kwargs.get(key) for key in builder.keys]
            )
            for builder in builders
        ]

    def _handle_decide(self, builder, kwargs):
        if len(inspect.getargspec(builder.decide).args) == 3:
            return builder.decide(builder.transform, kwargs, builder.keys)
        else:
            return builder.decide(kwargs)

    def _validate_incoming(self, kwargs):
        if not self.keys.issuperset(kwargs.keys()):
            raise TypeError("build() got unexpected keyword arguments: "
                            "{0}".format(', '.join(
                                repr(k) for k in kwargs.keys()
                                if k not in self.keys
                            )))

    def build(self, **kwargs):
        self._validate_incoming(kwargs)
        return {
            builder.output_key: builder.transform_from_kwargs(kwargs)
            for builder in self.builders
            if self._handle_decide(builder, kwargs)
        }

    def legacy_build(self, **kwargs):
        self._validate_incoming(kwargs)
        return {
            u'filter{0}'.format(filter_number): filter_string
            for filter_number, filter_string
            in enumerate(self.filters(**kwargs), 1)
        }

    def register_builder(self, filter_object):
        self.builders.append(filter_object)
        self.keys.update(filter_object.keys)
        self._update_docs_dict(self._key_to_string, filter_object.descriptions, filter_object.keys)
        self._update_docs_dict(self._key_to_values, filter_object.acceptable_values, filter_object.keys)
        self._update_docs_dict(self._key_to_type, filter_object.types, filter_object.keys)

    @util.curry
    def register_filter_builder(self, function, **kwargs):
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
        :param output_key: The key to use to output the provided value. Will
                           default to the only value in keys if keys has
                           length 1.
        :param keys: Keys that should be used as the argument names for
                     `function`, if none are provided, the filter functions
                     argument names will be used instead.
        :type keys: iterable of strings
        :param decider: a function of signature
                        `(function, incoming_keys, accepted_keys)` that returns
                        True if the filter function should be called and False
                        otherwise. Defaults to
                        :meth:`~.all_not_none_decider`
        :param descriptions: A description for the incoming filter function's
                             argument (or a list of descriptions if the filter
                             function takes multiple arguments)
        :param acceptable_values: An iterable of acceptable values for the parameter
                                  of the filter function (or a list of iterables if
                                  the filter function takes multiple parameters).
                                  Docstring will use the repr of the iterable's elements.
        :param types: The type (or a string describing the type) of the parameter accepted
                      by the incoming filter function (or a list of types if the function
                      takes multiple parameters)
        """
        kwargs['transform'] = function
        # assert 'decide' not in kwargs
        if 'decider' in kwargs:
            kwargs['decide'] = kwargs.pop('decider')
        return type('filter', (self.filter_class,), kwargs)

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
