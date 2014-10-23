# -*- coding: utf-8 -*-
import inspect
import logging
import re

from six import string_types

from . import helpers
from . import magicnumbers
from . import util
from .magicnumbers import maps
from .xpath import xpb


log = logging.getLogger(__name__)


class Detail(object):
    """Represent a detail belonging to an okcupid.com profile."""

    NO_DEFAULT = object()

    @classmethod
    def comma_separated_presenter(cls, text):
        return text.strip().split(', ')

    @classmethod
    def mapping_multi_updater(cls, mapping):
        def updater(id_name, value):
            if value is None:
                value = ()
            return {id_name: [mapping[item.lower()] for item in value]}
        return updater

    @classmethod
    def auto_indexed_updater(cls, *options):
        return cls.mapping_updater({option: index
                                    for index, option in enumerate(options, 1)},
                                   default=0)

    @classmethod
    def mapping_updater(cls, mapping, id_name=None):
        return cls(id_name=id_name,
                   updater=magicnumbers.MappingUpdater(mapping))

    @staticmethod
    def default_updater(id_name, value):
        return {id_name: value}

    def __init__(self, id_name=None, presenter=None, updater=None):
        self.id_name = id_name
        self.presenter = presenter or (lambda x: None if u'\u2014' in x
                                       else helpers.replace_chars(x.strip()))
        self.updater = updater or self.default_updater

    @property
    def id_name(self):
        return self._id_name

    _doc_format = 'The {0} detail of an okcupid.com user\'s profile.'
    @id_name.setter
    def id_name(self, value):
        self._id_name = value
        self.__doc__ = self._doc_format.format(self.id_name)

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
    """Represent the details belonging to an okcupid.com profile."""

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
            if not 'id' in value_element.attrib:
                continue
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

    bodytype = Detail.mapping_updater(maps.bodytype)
    orientation = Detail.mapping_updater(maps.orientation)
    smokes = Detail.mapping_updater(maps.smokes, id_name='smoking')
    drugs = Detail.mapping_updater(maps.drugs)
    drinks = Detail.mapping_updater(maps.drinks, id_name='drinking')
    job = Detail.mapping_updater(maps.job)
    status = Detail.mapping_updater(maps.status)
    monogamy = Detail(id_name='monogamous', updater=lambda id_name, value: {
        'monogamous': maps.monogamy[value],
        'monogamyflex': maps.strictness[value]
    })
    children = Detail(updater=lambda id_name, value: {
        'children': maps.has_kids[value],
        'children2': maps.wants_kids[value]
    })
    education = Detail(updater=lambda id_name, value: {
        'educationstatus': maps.education_status[value],
        'educationlevel': maps.education_level[value]
    })
    pets = Detail(updater=lambda id_name, value: {
        'cats': maps.cats[value],
        'dogs': maps.dogs[value]
    })
    diet = Detail(updater=lambda id_name, value: {
        'diet': maps.diet[value],
        'dietserious': maps.diet_strictness[value]
    })
    religion = Detail(updater=lambda id_name, value: {
        'religion': maps.religion[value],
        'religionserious': maps.seriousness[value]
    })
    sign = Detail(updater=lambda id_name, value: {
        'sign': maps.sign[value],
        'sign_status': maps.importance[value]
    })

    height = Detail(updater=lambda id_name, value: {
        'centimeters': int(round(magicnumbers.parse_height_string(value)))
    })

    class ethnicities(DeclarativeDetail):

        @staticmethod
        def presenter(text):
            return [ethnicity
                    for ethnicity in Detail.comma_separated_presenter(text)
                    if any(char.isalpha() for char in ethnicity)]

        @staticmethod
        def updater(id_name, value):
            if value is None:
                value = ()
            ethnicities = [maps.ethnicities[item.lower()] for item in value]
            if len(ethnicities) < 1:
                ethnicities = 10
            return {id_name: ethnicities}


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

    class languages(DeclarativeDetail):

        language_matcher = re.compile('(.*?) \((.*?)\)')

        language_to_number = magicnumbers.language_map_2

        level = util.IndexedREMap('fluently', 'okay', 'poorly')

        @classmethod
        def presenter(cls, value):
            language_strings = value.split(',')
            languages = []
            for language_string in language_strings:
                match = cls.language_matcher.match(language_string.strip())
                if match:
                    languages.append((match.group(1).lower(),
                                      match.group(2).lower()))
                else:
                    languages.append((language_string.strip(), None))
            return languages

        @classmethod
        def updater(cls, id_name, languages):
            data = {}
            number = 0
            for number, (language, level) in enumerate(languages, 1):
                language_number = cls.language_to_number[language.lower()]
                level = level or ''
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
