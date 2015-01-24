# -*- coding: utf-8 -*-
import itertools
import re

import six

from okcupyd import util
from okcupyd.question import UserQuestion


class maps(six.with_metaclass(util.GetAttrGetItem)):

    bodytype = util.IndexedREMap(
        'rather not say', 'thin', 'overweight', 'skinny', 'average', 'fit',
        'athletic', 'jacked', 'a little extra', 'curvy', 'full figured',
        'used up'
    )

    orientation = util.IndexedREMap('straight', 'gay', 'bisexual')

    smokes = util.IndexedREMap(
        'yes', 'sometimes', 'when drinking', 'trying to quit', 'no'
    )

    drugs = util.IndexedREMap('never', 'sometimes', 'often',
                              default=3, offset=0)

    drinks = util.IndexedREMap('very often', 'often', 'socially', 'rarely',
                               'desperately', 'not at all')

    ethnicities = util.IndexedREMap(
        'asian', 'middle eastern', 'black', 'native american', 'indian',
        'pacific islander', ('hispanic', 'latin'), 'white', 'other'
    )

    job = util.IndexedREMap(
        'student', ('art', 'music', 'writing'), ('banking', 'finance'),
        'administration', 'technology', 'construction', 'education',
        ('entertainment', 'media'), 'management', 'hospitality', 'law',
        'medicine', 'military', ('politics', 'government'),
        ('sales', 'marketing'), ('science', 'engineering'),
        'transportation', 'unemployed', 'other', 'rather not say',
        'retired'
    )

    status = util.IndexedREMap(
        'single', 'seeing someone', 'married', 'in an open relationship'
    )

    monogamy = util.IndexedREMap('(:?[^\-]monogamous)|(:?^monogamous)',
                                   'non-monogamous')
    strictness = util.IndexedREMap('mostly', 'strictly')

    # Doesn't want kids is index 6 for some reason.
    has_kids = util.IndexedREMap('has a kid', 'has kids', (), (), (),
                                 "doesn't have kids")
    wants_kids = util.IndexedREMap('might want', 'wants', "doesn't want")

    education_status = util.IndexedREMap('graduated', 'working', 'dropped out',
                                         default=0)
    education_level = util.IndexedREMap(
        'high ?school', 'two[- ]year college', 'university', 'college',
        'masters program', 'law school', 'med school', 'ph.d program',
        'space camp'
    )

    religion = util.IndexedREMap('agnosticism', 'atheism', 'christianity',
                                 'judaism', 'catholicism', 'islam', 'hinduism',
                                 'buddhism', 'other', default=1, offset=2)
    seriousness = util.IndexedREMap('very serious', 'somewhat serious',
                                    'not too serious', 'laughing')

    sign = util.IndexedREMap(
        'aquarius', 'pisces', 'aries', 'taurus', 'gemini', 'cancer', 'leo',
        'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn',
    )
    importance = util.IndexedREMap(
        "doesn't matter", "matters alot", "fun to think about"
    )

    dogs = util.REMap.from_string_pairs(
        (('dislikes dogs', 3), ('has dogs', 1), ('likes dogs', 2)),
        default=0
    )
    cats = util.REMap.from_string_pairs(
        (('dislikes cats', 3), ('has cats', 1), ('likes cats', 2)),
        default=0
    )
    language_level = util.IndexedREMap('fluently', 'okay', 'poorly')

    diet_strictness = util.IndexedREMap('[Mm]ostly', '[Ss]trictly')

    diet = util.IndexedREMap('anything', 'vegetarian', 'vegan',
                                  'kosher', 'halal', 'other')
    income = util.IndexedREMap(
        'less than $20,000', '$20,000-$30,000', '$30,000-$40,000',
        '$40,000-$50,000', '$50,000-$60,000', '$60,000-$70,000',
        '$70,000-$80,000', '$80,000-$100,000', '$100,000-$150,000',
        '$150,000-$250,000', '$250,000-$500,000', '$500,000-$1,000,000',
        'More than $1,000,000'
    )


class MappingUpdater(object):

    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, id_name, value):
        if isinstance(value, six.string_types):
            value = value.lower() # :/
        return {id_name: self.mapping[value]}


class SimpleFilterBuilder(object):

    def __init__(self, filter_number, mapping, offset=0):
        self.filter_number = filter_number
        self.mapping = mapping

    def get_number(self, values):
        acc = 0
        for value in values:
            acc += 2 ** int(self.mapping[value])
        return acc

    def get_filter(self, values):
        return '{0},{1}'.format(self.filter_number, self.get_number(values))

    __call__ = get_filter


class filters(six.with_metaclass(util.GetAttrGetItem)):

    bodytype = SimpleFilterBuilder(30, maps.bodytype)
    smokes = SimpleFilterBuilder(11, maps.smokes)
    drinks = SimpleFilterBuilder(12, maps.drinks)
    drugs = SimpleFilterBuilder(13, maps.drugs)
    education_level = SimpleFilterBuilder(19, maps.education_level)
    job = SimpleFilterBuilder(15, maps.job)
    income = SimpleFilterBuilder(14, maps.income)
    religion = SimpleFilterBuilder(8, maps.religion)
    monogamy = SimpleFilterBuilder(73, maps.monogamy)
    diet = SimpleFilterBuilder(54, maps.diet)
    sign = SimpleFilterBuilder(21, maps.sign)
    ethnicities = SimpleFilterBuilder(9, maps.ethnicities)
    dogs = SimpleFilterBuilder(16, maps.dogs)
    cats = SimpleFilterBuilder(17, maps.cats)


imperial_re = re.compile(u"([0-9])['′\u2032] ?([0-9][0-1]?)[\"″\u2033]",
                                 flags=re.UNICODE)
metric_re = re.compile(u"([0-2]\.[0-9]{1,2})m")


sep_replacements = ('\\', '/', '.', '-', ' ', '$', ',', '(', ')')


gentation_to_number = {
    'women who like men': '34',
    'women': '34',
    'men who like women': '17',
    'women who like women': '40',
    'men who like men': '20',
    'men and women who like bi men': '54',
    'men and women who like bi women': '57',
    'both who like bi men': '54',
    'both who like bi women': '57',
    'straight women only': '2',
    'straight men only': '1',
    'gay women only': '8',
    'gay men only': '4',
    'bi women only': '32',
    'bi men only': '16',
    'bi men and women': '48',
    'everybody': '63',
    'girls who like guys': '34',
    'guys who like girls': '17',
    'girls who like girls': '40',
    'guys who like guys': '20',
    'guys and girls who like bi guys': '54',
    'guys and girls who like bi girls': '57',
    'both who like bi guys': '54',
    'both who like bi girls': '57',
    'straight girls only': '2',
    'straight guys only': '1',
    'gay girls only': '8',
    'gay guys only': '4',
    'bi girls only': '32',
    'bi guys only': '16',
    'bi guys and girls': '48',
    'everybody': '63',
    '': '63'
}


looking_for_re_numbers = ((re.compile("[Ff]riends"), 1),
                          (re.compile("[Ll]ong.*[Dd]ating"), 2),
                          (re.compile("[Ss]hort.*[Dd]ating"), 3),
                          (re.compile("[Ss]ex"), 6))


def inches_to_centimeters(inches):
    return inches * 2.54


def get_height_filter(height_min=None, height_max=None):
    min_int = 0
    max_int = 99999
    if isinstance(height_min, six.string_types):
        min_int = 100 * parse_height_string(height_min)
    elif isinstance(height_min, int):
        min_int = 100 * inches_to_centimeters(height_min)
    if isinstance(height_max, six.string_types):
        max_int = 100 * parse_height_string(height_max)
    elif isinstance(height_max, int):
        max_int = 100 * inches_to_centimeters(height_max)
    return '10,{0},{1}'.format(min_int, max_int)


def parse_height_string(height_string):
    if not height_string:
        return 0
    match = imperial_re.search(height_string)
    if match:
        return int(round(inches_to_centimeters(int(match.group(1)) * 12 +
                                               int(match.group(2)))))
    match = metric_re.search(height_string)
    if match:
        meters = float(match.group(1))
        centimeters = meters * 100
        return int(round(centimeters))
    else:
        raise ValueError("The provided height did not match any of "
                         "the accepted formats.")


def get_kids_filter(has_kids=(), wants_kids=()):
    return '18,{0}'.format(get_kids_int(has_kids, wants_kids))


def get_kids_int(has_kids, wants_kids):
    has_kids = util.makelist(has_kids or ())
    wants_kids = util.makelist(wants_kids)
    wants_was_unknown = False
    has_was_unknown = False
    kids_int = 0
    has_kids_ints = [maps.has_kids[matchable] for matchable in has_kids]
    if len(has_kids_ints) == 0 or sum(has_kids_ints) == 0:
        has_kids_ints = list(maps.has_kids.values()) + [0]
        has_was_unknown = True
    wants_kids_ints = [maps.wants_kids[matchable] for matchable in wants_kids]
    if len(wants_kids_ints) == 0 or sum(wants_kids_ints) == 0:
        wants_kids_ints = list(maps.wants_kids.values()) + [0]
        wants_was_unknown = True
    wants_kids_ints = [v * 8 for v in wants_kids_ints]

    kids_int += sum(2 ** (hk_int + wk_int)
                    for hk_int, wk_int
                    in itertools.product(has_kids_ints, wants_kids_ints))

    if not (wants_was_unknown or has_was_unknown):
        # ... Why? Apparently this is needed...
        kids_int = subtract_has_kids_exponents(kids_int)

    # This is super crazy and gross. I'm not really sure why they do this.
    if not wants_was_unknown and has_was_unknown:
        if 3 in [maps.wants_kids[matchable] for matchable in wants_kids]:
            kids_int += 48

    return kids_int


def subtract_has_kids_exponents(value):
    has_kids_values = maps.has_kids.values()
    for exponent in yield_exponents_of_two(value):
        if exponent in has_kids_values:
            value -= exponent
    return value


def yield_exponents_of_two(value):
    power = 0
    while value > 0:
        if value & 0b1:
            yield power
        power += 1
        value >>= 1


def get_language_query(language):
    return '22,{0}'.format(language_map[language.lower()])


hour = 60*60
join_date_string_to_int = {
    'hour': hour,
    'day': hour*24,
    'week': hour*24*7,
    'month': hour*24*30,
    'year': 365*24*hour
}


def get_join_date_filter(join_date):
    date_int = 0
    if isinstance(join_date, str):
        if join_date in join_date_string_to_int:
            date_int = join_date_string_to_int[join_date]
        else:
            date_int = int(join_date)
    return '6,{0}'.format(date_int)


def get_question_filter(question, question_answers=None):
    question_id = question
    if isinstance(question, UserQuestion):
        question_id = question.id
    if question_answers is None:
        question_answers = [answer_option.id
                            for answer_option in question.answer_options
                            if answer_option.is_match]
    answers_int = 0
    for answer_int in question_answers:
        answers_int += 2 ** answer_int
    return '65,{0},{1}'.format(question_id, answers_int)


language_map_2 = {
    'afrikaans': 'af',
    'albanian': 'sq',
    'arabic': 'ar',
    'armenian': 'hy',
    'basque': 'eu',
    'belarusan': 'be',
    'bengali': 'bn',
    'breton': 'br',
    'bulgarian': 'bg',
    'catalan': 'ca',
    'cebuano': '11',
    'chechen': 'ce',
    'chinese': 'zh',
    'c++': '71',
    'croatian': 'hr',
    'czech': 'cs',
    'danish': 'da',
    'dutch': 'nl',
    'english': 'en',
    'esperanto': 'eo',
    'estonian': 'et',
    'farsi': '20',
    'finnish': 'fi',
    'french': 'fr',
    'frisian': '23',
    'georgian': '24',
    'german': 'de',
    'greek': 'el',
    'gujarati': 'gu',
    'ancient greek': '27',
    'hawaiian': '28',
    'hebrew': 'he',
    'hindi': 'hi',
    'hungarian': 'hu',
    'icelandic': 'is',
    'ilongo': '32',
    'indonesian': 'id',
    'irish': 'ga',
    'italian': 'it',
    'japanese': 'ja',
    'khmer': '37',
    'korean': 'ko',
    'latin': 'la',
    'latvian': 'lv',
    'lisp': '72',
    'lithuanian': 'lt',
    'malay': 'ms',
    'maori': 'mi',
    'mongolian': 'mn',
    'norwegian': 'no',
    'occitan': 'oc',
    'other': '73',
    'persian': 'fa',
    'polish': 'pl',
    'portuguese': 'pt',
    'romanian': 'ro',
    'rotuman': '51',
    'russian': 'ru',
    'sanskrit': 'sa',
    'sardinian': '54',
    'serbian': 'sr',
    'sign language': '1',
    'slovak': 'sk',
    'slovenian': 'sl',
    'spanish': 'es',
    'swahili': 'sw',
    'swedish': 'sv',
    'tagalog': 'tl',
    'tamil': 'ta',
    'thai': 'th',
    'tibetan': 'bo',
    'turkish': 'tr',
    'ukrainian': 'uk',
    'urdu': 'ur',
    'vietnamese': 'vi',
    'welsh': 'cy',
    'yiddish': 'yi'
}


language_map = {
    'afrikaans': '2',
    'albanian': '3',
    'ancient greek': '27',
    'arabic': '4',
    'armenian': '76',
    'basque': '5',
    'belarusan': '6',
    'bengali': '7',
    'breton': '8',
    'bulgarian': '9',
    'c++': '71',
    'catalan': '10',
    'cebuano': '11',
    'chechen': '12',
    'chinese': '13',
    'croatian': '14',
    'czech': '15',
    'danish': '16',
    'dutch': '17',
    'english': '74',
    'esperanto': '18',
    'estonian': '19',
    'farsi': '20',
    'finnish': '21',
    'french': '22',
    'frisian': '23',
    'georgian': '24',
    'german': '25',
    'greek': '26',
    'gujarati': '77',
    'hawaiian': '28',
    'hebrew': '29',
    'hindi': '75',
    'hungarian': '30',
    'icelandic': '31',
    'ilongo': '32',
    'indonesian': '33',
    'irish': '34',
    'italian': '35',
    'japanese': '36',
    'khmer': '37',
    'korean': '38',
    'lisp': '72',
    'latin': '39',
    'latvian': '40',
    'lithuanian': '41',
    'malay': '42',
    'maori': '43',
    'mongolian': '44',
    'norwegian': '45',
    'occitan': '46',
    'other': '73',
    'persian': '47',
    'polish': '48',
    'portuguese': '49',
    'romanian': '50',
    'rotuman': '51',
    'russian': '52',
    'sanskrit': '53',
    'sardinian': '54',
    'serbian': '55',
    'sign language': '1',
    'slovak': '56',
    'slovenian': '57',
    'spanish': '58',
    'swahili': '59',
    'swedish': '60',
    'tagalog': '61',
    'tamil': '62',
    'thai': '63',
    'tibetan': '64',
    'turkish': '65',
    'ukrainian': '66',
    'urdu': '67',
    'vietnamese': '68',
    'welsh': '69',
    'yiddish': '70',
}
