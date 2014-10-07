# -*- coding: utf-8 -*-
import inspect
import logging
import re

from six import string_types

from . import helpers
from . import magicnumbers
from . import util
from .xpath import xpb


log = logging.getLogger(__name__)


def IndexedREMap(*re_strings, **kwargs):
    default = kwargs.get('default', 0)
    offset = kwargs.get('offset', 1)
    string_index_pairs = []
    for index, string_or_tuple in enumerate(re_strings, offset):
        if isinstance(string_or_tuple, string_types):
            string_or_tuple = (string_or_tuple,)
        for re_string in string_or_tuple:
            string_index_pairs.append((re_string, index))
    return util.REMap.from_string_pairs(string_index_pairs, default=default)


class Detail(object):

    NO_DEFAULT = object()

    @classmethod
    def comma_separated_presenter(cls, text):
        return text.strip().split(', ')

    @classmethod
    def mapping_multi_updater(cls, mapping):
        def updater(id_name, value):
            return {id_name: [mapping[item.lower()] for item in value]}
        return updater

    @classmethod
    def auto_indexed_updater(cls, *options):
        return cls.mapping_updater({option: index
                                    for index, option in enumerate(options, 1)},
                                   default=0)

    @classmethod
    def mapping_updater(cls, mapping, default=NO_DEFAULT):
        def updater(id_name, value):
            if isinstance(value, string_types):
                value = value.lower() # :/
            try:
                update = mapping[value]
            except KeyError:
                if default is not cls.NO_DEFAULT:
                    update = default
                else:
                    raise
            return {id_name: update}
        return updater

    @staticmethod
    def default_updater(id_name, value):
        return {id_name: value}

    def __init__(self, id_name=None, presenter=None, updater=None):
        self.id_name = id_name
        self.presenter = presenter or (lambda x: None if u'\u2014' in x
                                       else helpers.replace_chars(x.strip()))
        self.updater = updater or self.default_updater

    def update(self, value):
        if isinstance(value, string_types):
            value = value.lower()
        return self.updater(self.id_name, value)

    def __get__(self, details, klass):
        if details is None:
            return self
        return self.presenter(details.id_to_display_name_value[self.id_name])

    def __set__(self, details, value):
        details.update(self.update(value))


class DeclarativeDetail(object):

    updater = None
    presenter = None


class Details(object):

    @classmethod
    def name_detail_pairs(cls):
        is_detail = lambda x: isinstance(x, Detail)
        return inspect.getmembers(cls, is_detail)

    def __init__(self, profile):
        self.profile = profile

    _profile_details_xpb = xpb.div(id='profile_details').dl

    def refresh(self):
        util.cached_property.bust_caches(self)

    @util.cached_property
    def id_to_display_name_value(self):
        output = {}
        for element in self._profile_details_xpb.apply_(
            self.profile.profile_tree
        ):
            value_element = xpb.dd.one_(element)
            id_name = value_element.attrib['id'].replace('ajax_', '')
            value = value_element.text_content()
            output[id_name] = value
        return output

    @property
    def as_dict(self):
        return {name: getattr(self, name)
                for name, _ in self.name_detail_pairs()}

    def convert_and_update(self, data):
        klass = type(self)
        server_bound = {}
        for key, value in data.items():
            detail = getattr(klass, key)
            server_bound.update(detail.update(value))
        return self.update(server_bound)

    def update(self, data):
        log.debug(data)
        response = self.profile.authcode_post('profileedit2', data=data)
        self.profile.refresh()
        self.refresh()
        return response

    bodytype = Detail(updater=Detail.mapping_updater({
        None: 0, u'—': 0, 'rather not say': 1, 'thin': 2, 'overweight': 3,
        'skinny': 4, 'average': 5, 'fit': 6, 'athletic': 7, 'jacked': 8,
        'a little extra': 9, 'curvy': 10, 'full figured': 11, 'used up': 12
    }))

    orientation = Detail(updater=Detail.mapping_updater({
        'straight': 1, 'gay': 2, 'bisexual': 3
    }))

    ethnicities = Detail(
        presenter=Detail.comma_separated_presenter,
        updater=Detail.mapping_multi_updater(IndexedREMap(
            'asian', 'middle eastern', 'black', 'native american', 'indian',
            'pacific islander', ('hispanic', 'latin'), 'white', 'other'
        ))
    )

    smoking = Detail(updater=Detail.auto_indexed_updater(
        'yes', 'sometimes', 'when drinking', 'trying to quit', 'no'
    ))

    drugs = Detail(updater=Detail.mapping_updater(IndexedREMap(
        'never', 'sometimes', 'often', default=3, offset=0
    )))

    drinking = Detail(updater=Detail.auto_indexed_updater(
        'very often', 'often', 'socially', 'rarely', 'desperately', 'not at all'
    ))

    job = Detail(updater=Detail.mapping_updater(IndexedREMap(
        'student', ('art', 'music', 'writing'), ('banking', 'finance'),
        'administration', 'technology', 'construction', 'education',
        ('entertainment', 'media'), 'management', 'hospitality', 'law',
        'medicine', 'military', ('politics', 'government'),
        ('sales', 'marketing'), ('science', 'engineering'),
        'transportation', 'unemployed', 'other', 'rather not say',
        'retired'
    )))

    status = Detail(updater=Detail.mapping_updater(IndexedREMap(
        'single', 'seeing someone', 'married', 'in an open relationship'
    )))

    class monogamous(DeclarativeDetail):

        monogamous = IndexedREMap('(:?[^\-]monogamous)|(:?^monogamous)',
                                  'non-monogamous')

        strictness = IndexedREMap('mostly', 'strictly')

        @classmethod
        def updater(cls, id_name, value):
            return {
                'monogamous': cls.monogamous[value],
                'monogamyflex': cls.strictness[value]
            }

    class children(DeclarativeDetail):

        # Doesn't want kids is index 6 for some reason.
        has_kids = IndexedREMap('has a kid', 'has kids', (), (), (),
                                "doesn't have kids")
        wants_kids = IndexedREMap('might want', 'wants', "doesn't want")

        @classmethod
        def updater(cls, id_name, value):
            return {'children': cls.has_kids[value],
                    'children2': cls.wants_kids[value]}

    class education(DeclarativeDetail):

        education_status = util.REMap.from_string_pairs(
            (('[Gg]raduated', 1),
             ('[Ww]orking', 2),
             ('[Dd]ropped out', 3),
             ('[Ss]ome', 3)),
            default=0
        )


        education_level = util.REMap(((re.compile('high ?school'), 1),
                                      (re.compile('two[- ]year college'), 2),
                                      (re.compile('university'), 3),
                                      (re.compile('college'), 3),
                                      (re.compile('masters program'), 4),
                                      (re.compile('law school'), 5),
                                      (re.compile('med school'), 6),
                                      (re.compile('ph.d program'), 7),
                                      (re.compile('space camp'), 8)), default=0)

        @classmethod
        def updater(cls, id_name, value):
            value = value.lower()
            status = cls.education_status[value]
            level = cls.education_level[value]
            return {'educationstatus': status, 'educationlevel': level}

    class height(DeclarativeDetail):

        imperial_re = re.compile(u"([0-9])['′\u2032] ?([0-9][0-1]?)[\"″\u2033]",
                                 flags=re.UNICODE)
        metric_re = re.compile(u"([0-2]\.[0-9]{2})m")

        @classmethod
        def updater(cls, id_name, value):
            match = cls.imperial_re.search(value)
            if match:
                return {'feet': match.group(1),
                        'inches': match.group(2)}

            match = cls.metric_re.search(value)
            if match:
                meters = float(match.group(1))
                centimeters = meters * 100
                return {'centimeters': int(centimeters)}
            else:
                raise ValueError("The provided height did not match any of "
                                 "the accepted formats.")

    class diet(DeclarativeDetail):

        diet_strictness = IndexedREMap('[Mm]ostly', '[Ss]trictly')

        diet_type = IndexedREMap('anything', 'vegetarian', 'vegan',
                                  'kosher', 'halal', 'other')

        @classmethod
        def updater(cls, id_name, value):
            return {'diet': cls.diet_type[value],
                    'dietserious': cls.diet_strictness[value]}

    class religion(DeclarativeDetail):

        religion = IndexedREMap('agnosticism', 'atheism', 'christianity',
                                'judaism', 'catholicism', 'islam', 'hinduism',
                                'buddhism', 'other', default=1, offset=2)
        seriousness = IndexedREMap('very serious', 'somewhat serious',
                                   'not too serious', 'laughing')

        @classmethod
        def updater(cls, id_name, value):
            return {'religion': cls.religion[value],
                    'religionserious': cls.seriousness[value]}

    class sign(DeclarativeDetail):

        sign = IndexedREMap(
            'aquarius', 'pisces', 'aries', 'taurus', 'gemini', 'cancer', 'leo',
            'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn',
        )

        importance = IndexedREMap(
            "doesn't matter", "matters alot", "fun to think about"
        )

        @classmethod
        def updater(cls, id_name, value):
            return {'sign': cls.sign[value],
                    'sign_status': cls.importance[value]}

    class income(DeclarativeDetail):

        levels = list(enumerate(
            (20000, 30000, 40000, 50000, 60000, 70000,
             80000, 100000, 150000, 250000, 500000, 1000000)
        ))

        comma_sep_number = '([0-9]{1,3}(?:,[0-9]{3})*)'

        range_matcher = re.compile(u'\$?{0}-\$?{0}'.format(comma_sep_number),
                                   flags=re.UNICODE)
        lt_matcher = re.compile("less than \$?{0}".format(comma_sep_number),
                                flags=re.UNICODE)
        gt_matcher = re.compile("more than \$?{0}".format(comma_sep_number),
                                flags=re.UNICODE)

        @classmethod
        def updater(cls, id_name, value):
            if value is None:
                return {'income': 0}
            if isinstance(value, string_types):
                for matcher, sign in ((cls.range_matcher, 1),
                                      (cls.lt_matcher, -1),
                                      (cls.gt_matcher, 1)):
                    match = matcher.match(value)
                    if match:
                        matched_income = int(match.group(1).replace(',', ''))
                        value = matched_income + 100 * sign
                        break
            for index, level in cls.levels:
                if value < level:
                    break
            else:
                index += 1
            update = index + 1
            return {'income': update}

    class pets(DeclarativeDetail):

        dogs = util.REMap.from_string_pairs(
            (('dislikes dogs', 3), ('has dogs', 1), ('likes dogs', 2)),
            default=0
        )

        cats = util.REMap.from_string_pairs(
            (('dislikes cats', 3), ('has cats', 1), ('likes cats', 2)),
            default=0
        )

        @classmethod
        def updater(cls, id_name, value):
            return {'cats': cls.cats[value],
                    'dogs': cls.dogs[value]}


    class languages(DeclarativeDetail):

        language_matcher = re.compile('(.*?) \((.*?)\)')

        language_to_number = magicnumbers.language_map_2

        level = {
            'fluently': 1, 'okay': 2, 'poorly': 3, None: 0
        }

        @classmethod
        def presenter(cls, value):
            language_strings = value.split(',')
            languages = []
            for language_string in language_strings:
                match = cls.language_matcher.match(language_string.strip())
                languages.append((match.group(1).lower(),
                                  match.group(2).lower()))
            return languages

        @classmethod
        def updater(cls, id_name, languages):
            data = {}
            for number, (language, level) in enumerate(languages, 1):
                language_number = cls.language_to_number[language.lower()]
                level_number = cls.level[level.lower()]
                data['cont_lang_{0}'.format(number)] = language_number
                data['language{0}status'.format(number)] = level_number
            number += 1
            for i in range(number, 6):
                data['cont_lang_{0}'.format(i)] = ''
                data['language{0}status'.format(i)] = ''
            return data


for id_name, detail in Details.name_detail_pairs():
    if detail.id_name is None:
        detail.id_name = id_name

    is_declarative_detail = lambda x: (isinstance(x, type) and
                                  issubclass(x, DeclarativeDetail))
    for id_name, declarative_detail in inspect.getmembers(
        Details, is_declarative_detail
    ):
        detail = Detail(presenter=declarative_detail.presenter,
                        updater=declarative_detail.updater,
                        id_name=id_name)
        setattr(Details, id_name, detail)
