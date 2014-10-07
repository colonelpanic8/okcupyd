# -*- coding: utf-8 -*-
import sys

import pytest

from okcupyd import User
from okcupyd import details
from okcupyd.util import REMap

from tests import util


sleep_time = 1


def get_re_map(updater):
    # lol... why am I doing this?
    closure_items = updater.func_closure
    for item in closure_items:
        item = item.cell_contents
        if isinstance(item, REMap):
            return item


@pytest.mark.skipif(sys.version_info > (3, 0),
                    reason="get_re_map doesn't work in python3")
@util.use_cassette
def test_job_detail(vcr_live_sleep):
    updater = details.Details.job.updater
    re_map = get_re_map(updater)
    user = User()
    user.profile.details.job = None
    assert user.profile.details.job == None
    for pattern, value in sorted(re_map.pattern_to_value.items()):
        user.profile.details.job = pattern
        vcr_live_sleep(sleep_time)
        assert pattern.lower() in user.profile.details.job.lower()
        assert updater('job', user.profile.details.job) == {'job': value}


@util.use_cassette
def test_height_detail(vcr_live_sleep):
    updater = details.Details.height.updater
    user = User()
    user.profile.details.height = "5'4\""
    vcr_live_sleep(sleep_time)
    assert user.profile.details.height == u'5\' 4" (1.63m)'
    assert updater('height', user.profile.details.height) == {
        'feet': '5', 'inches': '4'
    }
    vcr_live_sleep(sleep_time)
    user.profile.details.height = u'(1.99m)'
    vcr_live_sleep(sleep_time)
    assert user.profile.details.height == u'6\' 6" (1.99m)'

    user.profile.details.height = u"5′4″"
    vcr_live_sleep(sleep_time)
    assert u'5\' 4" (1.63m)'


@util.use_cassette
def test_income_detail(vcr_live_sleep):
    details = User().profile.details
    details.income = None
    vcr_live_sleep(sleep_time)
    assert details.income == None
    vcr_live_sleep(sleep_time)
    details.income = 55000
    vcr_live_sleep(sleep_time)
    assert details.income == u'$50,000-$60,000'

    details.income = u'$40,000-$50,000'
    vcr_live_sleep(sleep_time)
    assert details.income == u'$40,000-$50,000'
    vcr_live_sleep(sleep_time)

    details.income = u'More than $1,000,000'
    vcr_live_sleep(sleep_time)
    assert details.income == u'More than $1,000,000'
    vcr_live_sleep(sleep_time)

    details.income = u'Less than $20,000'
    vcr_live_sleep(sleep_time)
    assert details.income == u'Less than $20,000'


@util.use_cassette
def test_monogamous_detail(vcr_live_sleep):
    details = User().profile.details

    details.monogamous = None
    assert details.monogamous == None

    for fidelity_type in ('non-monogamous', 'monogamous'):
        for strictness in ('strictly', 'mostly'):
            details.monogamous = '{0} {1}'.format(strictness, fidelity_type)
            vcr_live_sleep(sleep_time)
            assert strictness in details.monogamous.lower()
            assert fidelity_type in details.monogamous.lower()


@util.use_cassette
def test_children_detail(vcr_live_sleep):
    details = User().profile.details
    details.children = None
    vcr_live_sleep(sleep_time)
    assert details.children == None
    vcr_live_sleep(sleep_time)

    details.children = u"has a kid, but doesn't want more"
    vcr_live_sleep(sleep_time)
    assert details.children == u"Has a kid, but doesn't want more"
    vcr_live_sleep(sleep_time)

    kids_string = u"Doesn't have kids, and doesn't want any"
    details.children = kids_string
    vcr_live_sleep(sleep_time)
    assert details.children == kids_string
    vcr_live_sleep(sleep_time)

    kids_string = u"Doesn't have kids, but might want them"
    details.children = kids_string
    vcr_live_sleep(sleep_time)
    assert details.children == kids_string
    vcr_live_sleep(sleep_time)

    details.children = 'Has kids'
    vcr_live_sleep(sleep_time)
    assert details.children == 'Has kids'


@util.use_cassette
def test_sign_detail(vcr_live_sleep):
    profile_details = User().profile.details
    profile_details.sign = None
    vcr_live_sleep(sleep_time)

    signs = ['aquarius', 'pisces', 'aries', 'taurus', 'gemini', 'cancer', 'leo',
             'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn']
    for sign in signs:
        profile_details.sign = sign
        vcr_live_sleep(sleep_time)
        assert sign in profile_details.sign.lower()
        vcr_live_sleep(sleep_time)
    profile_details.sign = 'Pisces, and it\'s fun to think about'
    vcr_live_sleep(sleep_time)
    assert 'fun' in profile_details.sign.lower()
    assert 'pisces' in profile_details.sign.lower()


@util.use_cassette
def test_pets_detail(vcr_live_sleep):
    details = User().profile.details
    for relationship in ('has', 'likes', 'dislikes'):
        for pet in ('cats', 'dogs'):
            details.pets = '{0} {1}'.format(relationship, pet)
            vcr_live_sleep(sleep_time)
            assert relationship in details.pets.lower()
            assert pet in details.pets.lower()
            vcr_live_sleep(sleep_time)
    details.pets = 'has cats likes dogs'
    vcr_live_sleep(sleep_time)
    assert details.pets.lower() == 'likes dogs and has cats'


@util.use_cassette
def test_languages_detail(vcr_live_sleep):
    details = User().profile.details

    values = [
        [('spanish', 'poorly'), ('english', 'fluently')],
        [('catalan', 'okay')],
        [('esperanto', 'fluently'), ('dutch', 'okay')],
    ]
    for value in values:
        details.languages = value
        vcr_live_sleep(sleep_time)
        assert details.languages == value
        vcr_live_sleep(sleep_time)


@util.use_cassette
def test_idempotence_and_convert_and_update_function(vcr_live_sleep):
    details = User().profile.details
    before = details.as_dict
    details.convert_and_update(before)
    vcr_live_sleep(sleep_time)
    assert before == details.as_dict


@util.use_cassette
def test_many_details(vcr_live_sleep):
    details = User().profile.details
    sample_details = {
        'job': 'technology',
        'diet': 'Strictly Vegetarian',
        'income': 40000,
        'bodytype': 'athletic',
        'orientation': 'bisexual',
        'ethnicities': ['Asian', 'White', 'hispanic', 'black'],
        'smoking': 'when drinking',
        'drugs': 'never',
        'drinking': 'desperately',
        'education': 'Some university',
        'height': '1.52m',
        'religion': 'atheism',
        'sign': 'aries and it matters a lot',
        'status': 'single'
    }

    details.convert_and_update(sample_details)
    vcr_live_sleep(sleep_time)


@util.use_cassette
def test_many_details_2(vcr_live_sleep):
    details = User().profile.details
    sample_details = {
        'income': 'Less than $20,000',
        'monogamous': 'Mostly monogamous',
        'pets': 'Likes dogs and has cats',
        'religion': 'Judaism, and very serious about it',
        'sign': "Pisces, and it's fun to think about",
        'children': "Doesn't have kids, but wants them",
        'drugs': 'Never'
    }
    details.convert_and_update(sample_details)
    vcr_live_sleep(sleep_time)
    for key, value in sorted(sample_details.items()):
        assert getattr(details, key) == value
