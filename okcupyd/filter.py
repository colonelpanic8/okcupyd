import inspect

from . import helpers
from . import magicnumbers
from . import util


class Filters(object):

    builder_to_keys = {}
    builder_to_decider = {}

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

    def __init__(self, **kwargs):
        self._options = kwargs

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, self._options)

    @property
    def filters(self):
        builders = [builder for builder, decider in self.builder_to_decider.items()
                    if decider(builder, self._options, self.builder_to_keys[builder])]
        return [builder(*[self._options.get(key)
                          for key in self.builder_to_keys[builder]])
                for builder in builders]

    def build(self):
        return {'filter{0}'.format(filter_number): filter_string
                for filter_number, filter_string in enumerate(self.filters, 1)}


    @classmethod
    @util.curry
    def register_filter_builder(cls, function, keys=(), decider=None):
        decider = decider or cls.all_not_none_decider
        function_arguments = inspect.getargspec(function).args
        if keys:
            assert len(keys) == len(function_arguments)
        else:
            keys = function_arguments
        cls.builder_to_keys[function] = keys
        cls.builder_to_decider[function] = decider

        return function


@Filters.register_filter_builder
def gentation_for_filter(gentation):
    return '0,{0}'.format(magicnumbers.gentation_to_number[gentation.lower()])


@Filters.register_filter_builder(decider=Filters.any_not_none_decider)
def age_filter(age_min=18, age_max=99):
    if age_min == None:
        age_min = 18
    return '2,{0},{1}'.format(age_min, age_max)


@Filters.register_filter_builder(decider=Filters.any_decider)
def attractiveness_filter(attractiveness_min, attractiveness_max):
    if attractiveness_min == None:
        attractiveness_min = 0
    if attractiveness_max == None:
        attractiveness_max = 10000
    return '25,{0},{1}'.format(attractiveness_min, attractiveness_max)


@Filters.register_filter_builder(decider=Filters.any_not_none_decider)
def height_filter(height_min, height_max):
    return magicnumbers.get_height_query(height_min, height_max)


@Filters.register_filter_builder
def last_online_filter(last_online):
    return '5,{0}'.format(helpers.format_last_online(last_online))


@Filters.register_filter_builder
def status_filter(status):
    status_int = 2  # single, default
    if status.lower() in ('not single', 'married'):
        status_int = 12
    elif status.lower() == 'any':
        status_int = 0
    return '35,{0}'.format(status_int)


@Filters.register_filter_builder
def location_filter(radius):
    return '3,{0}'.format(radius)


def build_option_filter(key):
    @Filters.register_filter_builder(keys=(key,))
    @util.makelist_decorator
    def option_filter(value):
        return magicnumbers.get_options_query(key, value)


for key in ['smokes', 'drinks', 'drugs', 'education', 'job',
            'income', 'religion', 'monogamy', 'diet', 'sign',
            'ethnicity']:
    build_option_filter(key)

pairs = [('pets', util.makelist_decorator(magicnumbers.get_pet_queries)),
         ('offspring', util.makelist_decorator(magicnumbers.get_kids_query)),
         ('join_date', magicnumbers.get_join_date_query),
         ('languages', magicnumbers.get_language_query)]
for key, function in pairs:

    Filters.register_filter_builder(keys=(key,))(function)
