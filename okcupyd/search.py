"""
Search OKCupid profiles, return a list of matching profiles.
See the search page on OKCupid for a better idea of the
arguments expected.
Parameters
----------
location : string, optional
    Location of profiles returned. Accept ZIP codes, city
    names, city & state combinations, and city & country
    combinations. Default to user location if unable to
    understand the string or if no value is given.
radius : int, optional
    Radius in miles searched, centered on the location.
number : int, optional
    Number of profiles returned. Default to 18, which is the
    same number that OKCupid returns by default.
age_min : int, optional
    Minimum age of profiles returned. Cannot be lower than 18.
age_max : int, optional
    Maximum age of profiles returned. Cannot be higher than 99.
order_by : str, optional
    Order in which profiles are returned.
last_online : str, optional
    How recently online the profiles returned are. Can also be
    an int that represents seconds.
status : str, optional
    Dating status of profiles returned. Default to 'single'
    unless the argument is either 'not single', 'married', or
    'any'.
height_min : int, optional
    Minimum height in inches of profiles returned.
height_max : int, optional
    Maximum height in inches of profiles returned.
looking_for : str, optional
    Describe the gender and orientation of profiles returned.
    If left blank, return some variation of "guys/girls who
    like guys/girls" or "both who like bi girls/guys, depending
    on the user's gender and orientation.
smokes : str or list of str, optional
    Smoking habits of profiles returned.
drinks : str or list of str, optional
    Drinking habits of profiles returned.
drugs : str or list of str, optional
    Drug habits of profiles returned.
education : str or list of str, optional
    Highest level of education attained by profiles returned.
job : str or list of str, optional
    Industry in which the profile users work.
income : str or list of str, optional
    Income range of profiles returned.
religion : str or list of str, optional
    Religion of profiles returned.
monogamy : str or list of str, optional
    Whether the profiles returned are monogamous or non-monogamous.
offspring : str or list of str, optional
    Whether the profiles returned have or want children.
pets : str or list of str, optional
    Dog/cat ownership of profiles returned.
languages : str or list of str, optional
    Languages spoken for profiles returned.
diet : str or list of str, optional
    Dietary restrictions of profiles returned.
sign : str or list of str, optional
    Astrological sign of profiles returned.
ethnicity : str or list of str, optional
    Ethnicity of profiles returned.
join_date : int or str, optional
    Either a string describing the profile join dates ('last
    week', 'last year' etc.) or an int indicating the number
    of maximum seconds from the moment of joining OKCupid.
keywords : str, optional
    Keywords that the profiles returned must contain. Note that
    spaces separate keywords, ie. `keywords="love cats"` will
    return profiles that contain both "love" and "cats" rather
    than the exact string "love cats".
"""
import inspect
import logging

from lxml import html
import simplejson

from . import helpers
from . import magicnumbers
from . import util
from .profile import Profile
from .session import Session
from .xpath import xpb


log = logging.getLogger(__name__)


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
    status_int = 2  # single, default
    if status.lower() in ('not single', 'married'):
        status_int = 12
    elif status.lower() == 'any':
        status_int = 0
    return '35,{0}'.format(status_int)


@register_filter_builder
def location_filter(radius):
    return '3,{0}'.format(radius)


def build_option_filter(key):
    @register_filter_builder(keys=(key,))
    @util.makelist_decorator
    def option_filter(value):
        return magicnumbers.get_options_query(key, value)



for key in ['smokes', 'drinks', 'drugs', 'education', 'job',
            'income', 'religion', 'monogamy', 'diet', 'sign',
            'ethnicity']:
    build_option_filter(key)


for key, function in [('pets', util.makelist_decorator(magicnumbers.get_pet_queries)),
                      ('offspring', util.makelist_decorator(magicnumbers.get_kids_query)),
                      ('join_date', magicnumbers.get_join_date_query),
                      ('languages', magicnumbers.get_language_query)]:

    register_filter_builder(keys=(key,))(function)


class SearchParameterBuilder(object):

    def __init__(self, **kwargs):
        self._options = kwargs

    @property
    def location(self):
        return self._options.get('location', None)

    @property
    def gender(self):
        return self._options.get('gender', 'm')

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
        self._options.update(kwargs)
        return self._options

    def build(self, session, count=9, low=None):
        search_parameters = {
            'timekey': 1,
            'matchOrderBy': self.order_by.upper(),
            'custom_search': '0',
            'fromWhoOnline': '0',
            'mygender': self.gender,
            'update_prefs': '1',
            'sort_type': '0',
            'sa': '1',
            'count': str(count),
            'locid': str(helpers.get_locid(session, self.location)) if self.location else 0,
            'ajax_load': 1,
            'discard_prefs': 1,
            'match_card_class': 'just_appended'
        }
        if low:
            search_parameters['low'] = low
        if self.keywords: search_parameters['keywords'] = self.keywords
        for filter_number, filter_string in enumerate(self.filters, 1):
            search_parameters['filter{0}'.format(filter_number)] = filter_string
        return search_parameters


class MatchCardExtractor(object):

    def __init__(self, div):
        self._div = div

    @property
    def username(self):
        return xpb.div.with_class('username').get_text_(self._div).strip()

    @property
    def age(self):
        return int(xpb.span.with_class('age').get_text_(self._div))

    @property
    def location(self):
        return helpers.replace_chars(
            xpb.span.with_class('location').get_text_(self._div)
        )

    _match_percentage_xpb = xpb.div.with_classes('percentage_wrapper', 'match').span.with_classes('percentage')

    @property
    def match_percentage(self):
        try:
            return int(self._match_percentage_xpb.get_text_(self._div).strip('%'))
        except:
            return 0

    _enemy_percentage_xpb = xpb.div.with_classes('percentage_wrapper', 'enemy').span.with_classes('percentage')

    @property
    def enemy_percentage(self):
        try:
            return int(self._enemy_percentage_xpb.get_text_(self._div).strip('%'))
        except ValueError:
            return 0

    @property
    def contacted(self):
        return bool(xpb.div.with_class('fancydate').apply_(self._div))

    @property
    def as_dict(self):
        return {
            'username': self.username,
            'age': self.age,
            'location': self.location,
            'match_percentage': self.match_percentage,
            'enemy_percentage': self.enemy_percentage,
            'id': self.id,
            'rating': self.rating,
            'contacted': self.contacted
        }


class SearchManager(object):

    def __init__(self, session=None, low=1, **kwargs):
        self._session = session or Session.login()
        self._parameter_builder = SearchParameterBuilder(**kwargs)
        self.set_options = self._parameter_builder.set_options
        self._low = low

    def get_search_html(self, count=9):
        search_parameters = self._parameter_builder.build(self._session,
                                                          count, self._low)
        log.info(simplejson.dumps({'search_parameters': search_parameters}))
        response = self._session.get('https://www.okcupid.com/match',
                                     params=search_parameters)
        try:
            search_html = response.json()['html']
        except:
            log.warning(simplejson.dumps(
                {'failure': response.content.decode('utf8')}
            ))
            raise
        return search_html

    def get_profiles(self, count=9):
        search_html = self.get_search_html(count)
        self._low += count
        if not search_html.strip(): return []
        tree = html.fromstring(search_html)
        match_card_elems = xpb.div.with_classes('match_card').apply_(tree)

        profiles = []
        for div in match_card_elems:
            match_card_extractor = MatchCardExtractor(div)
            profiles.append(Profile(self._session, match_card_extractor.username,
                                    age=match_card_extractor.age,
                                    location=match_card_extractor.location,
                                    match_percentage=match_card_extractor.match_percentage,
                                    enemy_percentage=match_card_extractor.enemy_percentage,
                                    contacted=match_card_extractor.contacted))
        return profiles



def search(session=None, count=9, **kwargs):
    return SearchManager(session, **kwargs).get_profiles(count)
