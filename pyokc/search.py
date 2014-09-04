import inspect

from . import helpers
from . import magicnumbers
from . import util


key_to_builders = {}
builder_to_keys = {}
builder_to_decider = {}


def any_decider(function, incoming_keys, accepted_keys):
    return bool(set(incoming_keys).intersection(accepted_keys))


def all_decider(function, incoming_keys, accepted_keys):
    return set(accepted_keys).issubset(incoming_keys)


@util.n_partialable
def register_filter_builder(function, keys=(), decider=all_decider):
    function_arguments = inspect.getargspec(function).args
    if keys:
        assert len(keys) == len(function_arguments)
    else:
        keys = function_arguments
    builder_to_keys[function] = keys
    for key in keys:
        assert key not in key_to_builders
        key_to_builders.setdefault(key, []).append(function)

    builder_to_decider[function] = decider

    return function


@register_filter_builder
def looking_for_filter(looking_for):
    return '0,{0}'.format(magicnumbers.seeking[looking_for.lower()])


@register_filter_builder(decider=any_decider)
def age_filter(age_min=18, age_max=99):
    if age_min == None:
        age_min = 18
    return '2,{0},{1}'.format(age_min, age_max)


@register_filter_builder(decider=any_decider)
def attractiveness_filter(attractiveness_min, attractiveness_max):
    if attractiveness_min == None:
        attractiveness_min = 0
    if attractiveness_max == None:
        attractiveness_max = 10000
    return '25,{0},{1}'.format(attractiveness_min, attractiveness_max)


@register_filter_builder(decider=any_decider)
def height_filter(height_min, height_max):
    return magicnumbers.get_height_query(height_min, height_max)


@register_filter_builder
def last_online_filter(last_online):
    return '5,{0}'.format(helpers.format_last_online(last_online))


@register_filter_builder
def status_filter(status):
    return '35,{0}'.format(helpers.format_status(status))


@register_filter_builder
def location_filter(radius):
    return '3,{0}'.format(radius)


for key in ['smokes', 'drinks', 'drugs', 'education', 'job',
            'income', 'religion', 'monogamy', 'diet', 'sign',
            'ethnicity']:
    @register_filter_builder(keys=(key,))
    @util.makelist_decorator
    def option_filter(value):
        magicnumbers.get_options_query(key, [value])


for key, function in [('pets', util.makelist_decorator(magicnumbers.get_pet_queries)),
                      ('offspring', util.makelist_decorator(magicnumbers.get_kids_query)),
                      ('join_date', magicnumbers.get_join_date_query),
                      ('languages', magicnumbers.get_language_query)]:

    @register_filter_builder(keys=(key,))
    def magicnumber_option_filter(value):
        return function(value)


class Search(object):

    def __init__(self, **kwargs):
        self._options = kwargs

    @property
    def location(self):
        return self._options.get('location', '')

    @property
    def gender(self):
        return self._options.get('gender', 'M')

    @property
    def keywords(self):
        return self._options.get('keywords')

    @property
    def order_by(self):
        return self._options.get('order_by', 'match').upper()

    @property
    def filters(self):
        incoming_keys = tuple(self._options.keys())
        builders = [builder for builder, decider in builder_to_decider.items()
                    if decider(builder, incoming_keys, builder_to_keys[builder])]
        return [builder(*[self._options.get(key) for key in builder_to_keys[builder]])
                for builder in builders]

    def set_options(self, **kwargs):
        self.options.update(kwargs)
        return self.options

    def basic_params(self):
        return {
            'locid': self.locid,
            'timekey': 1,
            'matchOrderBy': self.order_by.upper(),
            'custom_search': 0,
            'fromWhoOnline': 0,
            'mygender': self.gender,
            'update_prefs': 1,
            'sort_type': 0,
            'sa': 1,
            'using_saved_search': '',
        }

    def execute(self, session, count=9):
        search_parameters = self.basic_params()
        search_parameters['count'] = count
        if self.keywords: search_parameters['keywords'] = self.keywords
        for filter_number, filter_string in enumerate(self.filters, 1):
            search_parameters['filter{0}'.format(filter_number)] = filter_string

        return session.get('http://www.okcupid.com/match', data=search_parameters, headers=self.headers)
