import logging

import simplejson

from . import filter
from . import magicnumbers
from . import util
from .profile import Profile
from .session import Session
import six


log = logging.getLogger(__name__)


search_filters = filter.Filters()


def SearchFetchable(session=None, **kwargs):
    """Search okcupid.com with the given parameters. Parameters are
    registered to this function through
    :meth:`~okcupyd.filter.Filters.register_filter_builder` of
    :data:`~okcupyd.json_search.search_filters`.

    :returns: A :class:`~okcupyd.util.fetchable.Fetchable` of
              :class:`~okcupyd.profile.Profile` instances.

    :param session: A logged in session.
    :type session: :class:`~okcupyd.session.Session`
    :param order_by: The criteria to use for ordering search results.
                     Expected values: 'match', 'online', 'special_blend'
    """
    # TODO: to match SearchFetchable in html_search.py, we may want to provide
    # implementations handling the following keys:
    #    param location: A location string which will be used to filter results.
    #    param gender: The gender of the user performing the search.
    #    param keywords: A list or space delimeted string of words to search for.
    # Currently we just filter them out of kwargs and don't do anything with them.
    session = session or Session.login()
    return util.Fetchable(
        SearchManager(
            SearchJSONFetcher(session, **kwargs),
            ProfileBuilder(session)
        )
    )


class SearchManager(object):

    def __init__(self, search_fetchable, profile_builder):
        self._search_fetchable = search_fetchable
        self._profile_builder = profile_builder
        self._last_after = None

    def fetch(self, count=18):
        last_last_after = object()
        while last_last_after != self._last_after:
            last_last_after = self._last_after
            for profile in self.fetch_once(count=count):
                yield profile

    def fetch_once(self, count=18):
        response = self._search_fetchable.fetch(
            after=self._last_after, count=count
        )
        try:
            self._last_after = response['paging']['cursors']['after']
        except KeyError:
            log.warning(simplejson.dumps(
                {
                    'msg': "unable to get after cursor from response",
                    'response': response
                }
            )
        )
        for profile in self._profile_builder(response):
            yield profile


class SearchJSONFetcher(object):

    def __init__(self, session=None, order_by="MATCH", location=None, keywords=None, **options):
        self._session = session or Session.login()
        self._order_by = order_by.upper()
        if self._order_by not in ('MATCH', 'ONLINE', 'SPECIAL_BLEND'): # TODO: haven't verified that options other than 'MATCH' still work; the web interface no longer provides a way to modify this
            raise TypeError
        self._location = location # location string, haven't implemented
        self._keywords = keywords # list or space-delimited string of words to match, haven't implemented
        self._parameters = search_filters.build(**options)

    def _query_params(self, after=None, count=None):
        search_parameters = {
            'after': after,
            'limit': count,
            # other admin parameters
            'debug': 0,
            'username': "",
            'save_search': 1,
            'order_by': self._order_by,

            'i_want': None,
            'they_want': None,
            'tagOrder': [],

            # optional parameters
            'minimum_height': None,
            'maximum_height': None,
            'languages': 0,
            'speaks_my_language': 0, # TODO shall we make 1 the default?
            'ethnicity': [],
            'religion': [],
            'smoking': [],
            'drinking': [],
            'drugs': [],
            'education': [],
            'children': [],
            'interest_ids': [],
            'looking_for': [],
            'availability': "any",
            'monogamy': "unknown",
            'answers': [],

            # mandatory parameters
            'gender_tags': None,
            'orientation_tags': None,
            'minimum_age': 18,
            'maximum_age': 99,
            'located_anywhere': 0,
            'radius': 10, # TODO set from current user's profile?
            'gentation': [ 0 ], # TODO set from current user's profile?
            'last_login': 0,
            'lquery': "",
            'locid': 0, # FIXME what should default be?
            'location': None, # FIXME what should default be?
        }
        search_parameters.update(self._parameters)
        return {'_json': search_parameters}

    def fetch(self, after=None, count=18):
        search_parameters = self._query_params(after=after, count=count)
        log.info(simplejson.dumps({'search_parameters': search_parameters}))
        response = self._session.okc_get(
            'search', params=search_parameters
        )
        try:
            search_json = response.json()
        except:
            log.warning(simplejson.dumps({'failure': response.content}))
            raise
        return search_json


class ProfileBuilder(object):

    def __init__(self, session):
        self._session = session

    def __call__(self, response_dictionary):
        try:
            profile_infos = response_dictionary['data']
        except KeyError:
            log.warning(simplejson.dumps(
                {
                    'msg': "unable to get data from response",
                    'response': response_dictionary
                }
            )
        )
        else:
            for profile_info in profile_infos:
                yield Profile(self._session, profile_info["username"])


### Filters ###

# New keys: gender_sought, orientation_sought, interests, kinds (last is already attribute on profile.looking_for, together with gentation and ages and single and near_me)

# These keys were available with the former html_search API, but no corresponding field has yet been observed
# on the new json_search API: job, income, diet, sign, cats, dogs, join_date, question_count_min, keywords

## :param job: expected values: 'art', 'sales', 'engineering', 'politics', 'education', 'technology', 'management', 'entertainment', 'media', 'administration', 'writing', 'other', 'music', 'medicine', 'transportation', 'finance', 'retired', 'government', 'marketing', 'unemployed', 'construction', 'student', 'hospitality', 'law', 'rather not say', 'science', 'banking', 'military'
## :type job: str
##
## :param income: expected values: '$30,000-$40,000', '$20,000-$30,000', '$80,000-$100,000', '$100,000-$150,000', '$250,000-$500,000', 'less than $20,000', 'More than $1,000,000', '$500,000-$1,000,000', '$60,000-$70,000', '$70,000-$80,000', '$40,000-$50,000', '$50,000-$60,000', '$150,000-$250,000'
## :type income: str
##
## :param diet: expected values: 'anything', 'vegetarian', 'vegan', 'kosher', 'other', 'halal'
## :type diet: str
##
## :param sign: expected values: 'libra', 'sagittarius', 'cancer', 'scorpio', 'aquarius', 'taurus', 'leo', 'virgo', 'capricorn', 'gemini', 'aries', 'pisces'
## :type sign: str
##
## :param cats: expected values: 'likes cats', 'dislikes cats', 'has cats'
## :type cats: str
##
## :param dogs: expected values: 'dislikes dogs', 'has dogs', 'likes dogs'
## :type dogs: str
##
## :param join_date: expected values: 'week', 'year', 'day', 'hour', 'month'
## :type join_date: int
##
## :param question_count_min: The minimum number of questions answered by returned search results.
## :type question_count_min: int


# This key is available on profile.looking_for, but no corresponding field has yet been observed
# on the new json_search API: single: True (is the target only looking for single matches?)



# Mandatory criteria

class LastLoginFilter(search_filters.filter_class):
    output_key = "last_login"
    description = "How recently returned search results must have been online."
    accepted_values = ('hour', 'day', 'today', 'week', 'month', 'year', 'decade')
    types = "string or an int specifying number of seconds"
    def transform(last_online):
        return(helpers.format_last_online(last_online))

class RadiusFilter(search_filters.filter_class):
    output_key = "radius"
    decide = search_filters.all_decider # permit radius=None
    description = "The maximum distance from the specified location of returned search results."
    types = "int or None"
    def transform(radius):
        return radius

class NearnessFilter(search_filters.filter_class):
    output_key = "located_anywhere"
    decide = search_filters.all_decider # permit radius=None
    description = "The maximum distance from the specified location of returned search results."
    types = "int or None"
    def transform(radius):
        return 1 if radius is None else 0

class MinAgeFilter(search_filters.filter_class):
    output_key = "minimum_age"
    description = "The minimum age of returned search results."
    types = int
    # TODO: also permit single key `ages=(age_min, age_max)`, as in looking_for.py?
    def transform(age_min=18):
        return age_min

class MaxAgeFilter(search_filters.filter_class):
    output_key = "maximum_age"
    description = "The maximum age of returned search results."
    types = int
    # TODO: also permit single key `ages=(age_min, age_max)`, as in looking_for.py?
    def transform(age_max=99):
        return age_max

# Gender/orientation filters

# These are interdependent in complex ways. See https://github.com/IvanMalison/okcupyd/issues/63#issuecomment-128243668.
# For input keys, we honor the old-style `gentation` key as well as new `gender_sought` and `orientation_sought`
# keys, which can be either strings or lists of strings, matching the new search interface on OKCupid's website.
# In future we may want to also honor input from the `gender` key to SearchFetchable (which specifies the
# logged-in user's gender, not the gender sought).
# For output, these set the `gender_tags`, `orientation_tags`, `gentation`, `i_want` and `they_want` fields
# in requests, in complex ways. We may be able to get away with omitting some of these fields; that's not
# known yet.

def accumulate_tags(keys, magicmap):
    acc = 0
    for k in keys:
        i = magicmap[k]
        if i is not None and i >= 0:
            acc += 2 ** i
        elif i < 0 or k.lower() in ('all', 'everyone', 'everybody', 'any'):
            acc = 0
            break
        else:
            raise TypeError
    return acc

# TODO also exploit `gender`?
class GenderFilter(search_filters.filter_class):
    output_key = "gender_tags"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", str)
    def transform(gender_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            if gent & (1+4+16):
                if gent & (2+8+32):
                    gender_sought = 'all'
                else:
                    gender_sought = 'men'
            elif gent & (2+8+32):
                gender_sought = 'women'
            else:
                gender_sought = 'all'
        return accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)

# TODO also exploit `gender`?
class OrientationFilter(search_filters.filter_class):
    output_key = "orientation_tags"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.orientation_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", str)
    def transform(orientation_sought, gentation):
        if gentation is not None:
            assert orientation_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            orientation_sought = []
            if gent & (1+2):
                orientation_sought.add('straight')
            if gent & (4+8):
                orientation_sought.add('gay')
            if gent & (16+32):
                orientation_sought.add('bisexual')
        return accumulate_tags(makelist(orientation_sought), magicnumbers.maps.orientation_tags)

# TODO also exploit `gender`?
class IWantFilter(search_filters.filter_class):
    output_key = "i_want"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", str)
    def transform(gender_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            if gent & (1+4+16):
                if gent & (2+8+32):
                    gender_sought = 'all'
                else:
                    gender_sought = 'men'
            elif gent & (2+8+32):
                gender_sought = 'women'
            else:
                gender_sought = 'all'
        gen = accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)
        if gen > 3:
            return 'other'
        assert gen >= 0
        return {0: 'everyone', 1:'women', 2:'men', 3:'other'}[gen]

# TODO also exploit `gender`?
class TheyWantFilter(search_filters.filter_class):
    output_key = "they_want"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.maps.orientation_tags.keys(),
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", "string or list of strings", str)
    def transform(gender_sought, orientation_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            assert orientation_sought is None
            gentation = gentation.strip().lower()
            gent = magicnumbers.gentation_to_number[gentation]
            if gent & (1+4+16):
                if gent & (2+8+32):
                    gender_sought = 'all'
                else:
                    gender_sought = 'men'
            elif gent & (2+8+32):
                gender_sought = 'women'
            else:
                gender_sought = 'all'
            orientation_sought = []
            if gent & (1+2):
                orientation_sought.add('straight')
            if gent & (4+8):
                orientation_sought.add('gay')
            if gent & (16+32):
                orientation_sought.add('bisexual')
        orient = accumulate_tags(makelist(orientation_sought), magicnumbers.maps.orientation_tags)
        if orient > 3:
            return 'other'
        gen = accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)
        if gen == 1:
            return {0: 'other', 1: 'men', 2: 'women', 3: 'other'}[orient]
        elif gen == 2:
            return {0: 'other', 1: 'women', 2: 'men', 3: 'other'}[orient]
        else:
            return 'other'

# TODO also exploit `gender`?
class GentationFilter(search_filters.filter_class):
    output_key = "gentation"
    decide = search_filters.any_not_none_decider
    acceptable_values = (magicnumbers.maps.gender_tags.keys(), # also 'all', 'everyone', 'everybody', 'any'
                        magicnumbers.maps.orientation_tags.keys(),
                        magicnumbers.gentation_to_number.keys())
    types = ("string or list of strings", "string or list of strings", str)
    def transform(gender_sought, orientation_sought, gentation):
        if gentation is not None:
            assert gender_sought is None
            assert orientation_sought is None
            gentation = gentation.strip().lower()
        else:
            # convert gender_sought and orientation_sought to gentation
            gen = accumulate_tags(makelist(gender_sought), magicnumbers.maps.gender_tags)
            orient = accumulate_tags(makelist(orientation_sought), magicnumbers.maps.orientation_tags)
            gentation = {
                # all genders
                0: {0: 'everybody', 1: 'everybody', 2: 'everybody', 3: 'everybody', 4: 'bi men and women',
                    5: 'everybody', 6: 'everybody', 7: 'everybody'},
                # women
                1: {0: 'women',
                    1: 'straight women only',
                    2: 'gay women only',
                    3: 'women',
                    4: 'bi women only',
                    5: 'women who like men',
                    6: 'women who like women',
                    7: 'women'},
                # men
                2: {0: 'men',
                    1: 'straight men only',
                    2: 'gay men only',
                    3: 'men',
                    4: 'bi men only',
                    5: 'men who like women',
                    6: 'men who like men',
                    7: 'men'},
                # women and men
                3: {0: 'everybody', 1: 'everybody', 2: 'everybody', 3: 'everybody', 4: 'bi men and women',
                    5: 'everybody', 6: 'everybody', 7: 'everybody'},
            }[gen & 3][orient & 7]
        return [magicnumbers.gentation_to_number.get(gentation, gentation)]


# Optional criteria

class MinHeightFilter(search_filters.filter_class):
    output_key = "minimum_height"
    decide = search_filters.any_not_none_decider
    descriptions = ("The minimum height of returned search results.",
                    "The maximum height of returned search results.")
    types = ("a height int in inches, an imperial height string (5'0\"), or a metric height string (1.5m)",
             "a height int in inches, an imperial height string (5'0\"), or a metric height string (1.5m)")
    def transform(height_min, height_max=None):
        if isinstance(height_min, six.string_types):
            return 100 * magicnumbers.parse_height_string(height_min)
        elif isinstance(height_min, int):
            return 100 * magicnumbers.inches_to_centimeters(height)
        elif height_min is None:
            # 48" is 121.92 cm
            return 12192 # this will be called if height_max is specified but height_min isn't
        raise TypeError

class MaxHeightFilter(search_filters.filter_class):
    output_key = "maximum_height"
    decide = search_filters.any_not_none_decider
    descriptions = ("The minimum height of returned search results.",
                    "The maximum height of returned search results.")
    types = ("a height int in inches, an imperial height string (5'0\"), or a metric height string (1.5m)",
             "a height int in inches, an imperial height string (5'0\"), or a metric height string (1.5m)")
    def transform(height_max, height_min=None):
        if isinstance(height_max, six.string_types):
            return 100 * magicnumbers.parse_height_string(height_max)
        elif isinstance(height_max, int):
            return 100 * magicnumbers.inches_to_centimeters(height)
        elif height_max is None:
            return 99999 # this will be called if height_min is specified but height_max isn't
        raise TypeError

# TODO: permit specifying multiple languages?
# TODO: permit toggling speaks_my_language?
class LanguageFilter(search_filters.filter_class):
    output_key = "languages"
    # descriptions = "A single long-form language that search results must match."
    acceptable_values = magicnumbers.language_map.keys()
    # types = str
    def transform(language):
        # defaults to 0; also speaks_my_language can be 1 or 0
        return magicnumbers.language_map[language.lower()]

class StatusFilter(search_filters.filter_class):
    output_key = "availability"
    description = "The relationship status of returned search results."
    acceptable_values = ("single", "not single", "married", 'any')
    # types = str
    def transform(status="any"):
        status = status.lower()
        if status == 'not single' or status == 'married':
            return 'not_single'
        elif status in ('single', 'any'):
            return status
        else:
            raise TypeError

class MonogamyFilter(search_filters.filter_class):
    output_key = "monogamy"
    acceptable_values = ("yes", True, "no", False, 'monogamous', 'non-monogamous', 'any')
    # types = str
    def transform(monogamy="unknown"):
        # default is 'unknown'
        if isinstance(monogamy, six.string_types):
            monogamy = monogamy.lower()
        if monogamy in ('yes', True, 'monogamous'):
            return 'yes'
        elif monogamy in ('no', False, 'non-monogamous'):
            return 'no'
        elif monogamy == 'any':
            return 'unknown' # default
        else:
            raise TypeError

class LookingForFilter(search_filters.filter_class):
    output_key = "looking_for"
    # description = "One or more relationship types sought that search results must match."
    acceptable_values = (
        'new friends', 'short-term', 'short-term dating',
        'long-term', 'long-term dating', 'casual sex',
        'sex', 'any')
    types = "string or list of strings"
    @util.makelist_decorator
    def transform(kinds=[]):
        result = []
        for k in kinds:
            k = k.lower()
            if k == 'new friends':
                result.add('new_friends')
            elif k == 'short-term' or k == 'short-term dating':
                result.add('short_term_dating')
            elif k == 'long-term' or k == 'long-term dating':
                result.add('long_term_dating')
            elif k == 'casual sex' or k == 'sex':
                result.add('casual_sex')
            elif k != 'any':
                raise TypeError
            else: result.extend(('new_friends', 'short_term_dating', 'long_term_dating', 'casual_sex')) # or []
        return result

## old param keywords: A list or space-delimeted string of words to search for.
## new param interests: A list of ints or str(int)
class InterestsFilter(search_filters.filter_class):
    output_key = "interest_ids"
    description = "One or more interest ints that search results must match."
    types = "int or intstring, or list of such"
    @util.makelist_decorator
    def transform(interests=[]):
        for k in interests:
            int(k) # verify that each element converts to an int
        # expected to be list of bigint strings
        return interests

class EducationFilter(search_filters.filter_class):
    output_key = "education"
    # description = "One or more education levels that search results must match."
    acceptable_values = (
        'high school', 'two-year college', 'college', 'university', 'college/university',
        'post-grad', 'masters program', 'law school', 'med school', 'ph.d program'
        )
    types = "string or list of strings"
    # TODO: also permit shorter key `education`?
    @util.makelist_decorator
    def transform(education_level=[]):
        education = []
        for k in education_level:
            k = k.lower()
            i = magicnumbers.maps.education_level[k]
            if i == 1:
                education.add('high_school')
            elif i == 2:
                education.add('two_year_college')
            elif i == 3 or i == 4 or k == 'college/university':
                education.add('college_university')
            elif i in (5,6,7,8) or k == 'post-grad' or k == 'post grad' or k == 'grad':
                education.add('post_grad')
            else:
                # i == 9 when k == 'space camp', or unrecognized k
                raise TypeError
        return education

class ChildrenFilter(search_filters.filter_class):
    output_key = "children"
    decide = search_filters.any_not_none_decider
    acceptable_values = ((True, 'has a kid', 'has kids', False, "doesn't have a kid", "doesn't have kids"),
                         (True, 'wants', 'wants kids', False, "doesn't want", "doesn't want kids",
                         'might want', 'might want kids'))
    # types = (str, str)
    # TODO: also permit single key `kids`?
    def transform(has_kids=None, wants_kids=None):
        children = []
        if isinstance(has_kids, six.string_types):
            has_kids = has_kids.lower()
        if isinstance(wants_kids, six.string_types):
            wants_kids = wants_kids.lower()
        if has_kids == 'has a kid' or has_kids == 'has kids' or has_kids is True:
            children.append('has_one_or_more')
        elif has_kids == "doesn't have a kid" or has_kids == "doesn't have kids" or has_kids is False:
            children.append('doesnt_have')
        elif has_kids is not None:
            raise TypeError
        # else: children.extend(('has_one_or_more', 'doesnt_have'))
        if wants_kids == 'wants' or wants_kids == 'wants kids':
            children.append('wants_kids')
        elif wants_kids == "doesn't want" or wants_kids == "doesn't want kids":
            children.append('doesnt_want')
        elif wants_kids == 'might want' or wants_kids == 'might want kids':
            children.append('might_want')
        elif wants_kids is True:
            children.extend(('wants_kids', 'might_want'))
        elif wants_kids is False:
            children.extend(('doesnt_want', 'might_want'))
        elif wants_kids is not None:
            raise TypeError
        # else: children.extend(('wants_kids', 'might_want', 'doesnt_want'))
        return children

def normalform(keys, magicmap):
    result = []
    for k in keys:
        i = magicmap[k]
        result.append(magicmap.values[i])
    return result

class EthnicitiesFilter(search_filters.filter_class):
    output_key = "ethnicity"
    # description = "One or more ethnicities that search results must match."
    acceptable_values = (
        'asian',  'black', 'hispanic', 'hispanic/latin', 'indian', 'latin',
        'middle eastern', 'native american', 'pacific islander',
        'white', 'other')
    types = "string or list of strings"
    @util.makelist_decorator
    def transform(ethnicities=[]):
        return normalform(ethnicities, magicnumbers.maps.ethnicities)

class ReligionFilter(search_filters.filter_class):
    # output_key = "religion"
    # description = "One or more religions that search results must match."
    acceptable_values = magicnumbers.maps.religion.keys()
    types = "string or list of strings"
    @util.makelist_decorator
    def transform(religion=[]):
        return normalform(religion, magicnumbers.maps.religion)

class SmokingFilter(search_filters.filter_class):
    output_key = "smoking"
    # description = "One or more smoking frequencies that search results must match."
    acceptable_values = magicnumbers.maps.smokes.keys()
    types = "string or list of strings"
    @util.makelist_decorator
    def transform(smokes=[]):
        return normalform(smokes, magicnumbers.maps.smokes)

class DrinkingFilter(search_filters.filter_class):
    output_key = "drinking"
    # description = "One or more drinking frequencies that search results must match."
    acceptable_values = magicnumbers.maps.drinks.keys()
    types = "string or list of strings"
    @util.makelist_decorator
    def transform(drinks=[]):
        return normalform(drinks, magicnumbers.maps.drinks)

class DrugsFilter(search_filters.filter_class):
    # output_key = "drugs"
    # description = "One or more drug-taking frequencies that search results must match."
    acceptable_values = magicnumbers.maps.drugs.keys()
    types = "string or list of strings"
    @util.makelist_decorator
    def transform(drugs=[]):
        return normalform(drugs, magicnumbers.maps.drugs)


# These former keys may be available on the json_search API, but aren't implemented here
# because this author doesn't have an A-list account to experiment with:
# attractiveness_min, attractiveness_max, bodytype, question, question_answers

## :param attractiveness_max: The maximum attractiveness of returned search results.
## :type attractiveness_max: int
##
## :param attractiveness_min: The minimum attractiveness of returned search results.
## :type attractiveness_min: int
##
## :param bodytype: expected values: 'jacked', 'rather not say', 'fit', 'athletic', 'used up', 'average', 'full figured', 'overwe
## ight', 'curvy', 'thin', 'a little extra', 'skinny'
## :type bodytype: str
##
## :param question: A question whose answer should be used to match search results, or a question id. If a question id, `question_answers` must be supplied.
## :type question: :class:`~okcupyd.question.UserQuestion`
##
## :param question_answers: A list of acceptable question answer indices.
## :type question_answers: list

# There will presumably also be new keys for personality pluses/minuses, but this needs A-list


search_filters.add_to_docstring_of(SearchFetchable)
