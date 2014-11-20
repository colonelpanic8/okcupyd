import collections
import functools
import logging
import re

import simplejson

from . import magicnumbers
from . import util
from . import filter
from .xpath import xpb


log = logging.getLogger(__name__)


looking_for_filters = filter.Filters()
looking_for_filters.register_filter_builder(filter.gentation_filter)
looking_for_filters.register_filter_builder(filter.location_filter)
looking_for_filters.register_filter_builder(
    filter.age_filter,
    decider=filter.Filters.any_not_none_decider
)
@looking_for_filters.register_filter_builder(decider=filter.Filters.any_decider)
def status_filter(status):
    return '7,{0}'.format(int(status))


class LookingFor(object):
    """Represent the looking for attributes belonging to an okcupid.com
    profile.
    """

    _ages_re = re.compile(u'Ages ([0-9]{1,3})\u2013([0-9]{1,3})')

    _looking_for_xpb = xpb.div.with_classes('text', 'what_i_want')

    def __init__(self, profile):
        self._profile = profile

    @util.cached_property
    def raw_fields(self):
        li_elements = self._looking_for_xpb.li.apply_(
            self._profile.profile_tree
        )
        return {li.attrib['id'].split('_')[1]: li.text_content()
                for li in li_elements}

    def update_property(function):
        @property
        @functools.wraps(function)
        def wrapped(self):
            return function(self)

        @wrapped.setter
        def wrapped_setter(self, value):
            self.update(**{function.__name__: value})

        return wrapped_setter

    @update_property
    def gentation(self):
        """The sex/orientation that the user is looking for."""
        return self.raw_fields.get('gentation').lower().strip()

    @update_property
    def ages(self):
        """The age range that the user is interested in."""
        match = self._ages_re.match(self.raw_fields.get('ages'))
        return self.Ages(int(match.group(1)), int(match.group(2)))

    @update_property
    def single(self):
        """Whether or not the user is only interested in people that are single.
        """
        return 'display: none;' not in self._looking_for_xpb.li(id='ajax_single').\
            one_(self._profile.profile_tree).attrib['style']

    @update_property
    def near_me(self):
        """Whether the user is only interested in people that are close to them.
        """
        return 'near' in self.raw_fields.get('near', '').lower().strip()

    @update_property
    def kinds(self):
        """The kinds of relationship tha the user is looking for."""
        return self.raw_fields.get('lookingfor', '').\
            replace('For', '').strip().split(', ')

    def update(self, ages=None, single=None, near_me=None, kinds=None,
               gentation=None):
        """Update the looking for attributes of the logged in user.

        :param ages: The ages that the logged in user is interested in.
        :type ages: tuple
        :param single: Whether or not the user is only interested in people that
                       are single.
        :type single: bool
        :param near_me: Whether or not the user is only interested in
                        people that are near them.
        :type near_me: bool
        :param kinds: What kinds of relationships the user should be updated to
                      be interested in.
        :type kinds: list
        :param gentation: The sex/orientation of people the user is interested
                          in.
        :type gentation: str
        """
        ages = ages or self.ages
        single = single if single is not None else self.single
        near_me = near_me if near_me is not None else self.near_me
        kinds = kinds or self.kinds
        gentation = gentation or self.gentation
        data = {
            'okc_api': '1',
            'searchprefs.submit': '1',
            'update_prefs': '1',
            'lquery': '',
            'locid': '0',
            'filter5': '1, 1' # TODO(@IvanMalison) Do this better...
        }
        if kinds:
            kinds_numbers = self._build_kinds_numbers(kinds)
            if kinds_numbers:
                data['lookingfor'] = kinds_numbers
        age_min, age_max = ages
        data.update(looking_for_filters.build(
            status=single, gentation=gentation, radius=25 if near_me else 0,
            age_min=age_min, age_max=age_max
        ))
        log.info(simplejson.dumps({'looking_for_update': data}))
        util.cached_property.bust_caches(self)
        response = self._profile.authcode_post('profileedit2', data=data)
        self._profile.refresh(reload=False)
        return response.content

    @staticmethod
    def _build_kinds_numbers(looking_for_items):
        looking_for_numbers = []
        if not isinstance(looking_for_items, collections.Iterable):
            looking_for_numbers = (looking_for_items,)
        for item in looking_for_items:
            for matcher, number in magicnumbers.looking_for_re_numbers:
                if matcher.search(item) is not None:
                    looking_for_numbers.append(number)
        return looking_for_numbers

    del update_property
    Ages = collections.namedtuple('Ages', ('min', 'max'))
