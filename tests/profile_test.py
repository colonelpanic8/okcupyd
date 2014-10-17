# -*- coding: utf-8 -*-
import datetime

from . import util
from okcupyd import looking_for
from okcupyd import profile
from okcupyd import session
from okcupyd import User
from okcupyd.util import cached_property


@util.use_cassette
def test_profile_essays():
    user_profile = profile.Profile(session.Session.login(), 'FriedLiverAttack')
    assert user_profile.essays.self_summary


@util.use_cassette
def test_rate_profile():
    profile = User().quickmatch()
    profile.rate(5)
    profile.refresh()
    assert profile.rating == 5


@util.use_cassette
def test_rate_profile_1_stars():
    profile = User().quickmatch()
    profile.rate(1)
    assert User().get_profile(profile.username).rating == profile.rating
    assert profile.rating == 1


@util.use_cassette
def test_profile_properties():
    profile = User().quickmatch()
    assert 0 <= profile.match_percentage <= 100
    assert 0 <= profile.enemy_percentage <= 100
    assert profile.responds
    assert profile.contacted == False # We want it to be false, not falsy


@util.use_cassette
def test_profile_attractiveness():
    profile = User().search(attractiveness_min=3000, count=1)[0]
    assert 1 < profile.attractiveness < 10001


@util.use_cassette
def test_profile_contacted():
    profile = User().quickmatch()
    profile.message('test')
    assert bool(profile.contacted)
    assert isinstance(profile.contacted, datetime.datetime)


@util.use_cassette
def test_profile_on_inbox_correspondent():
    profile = User().outbox[-1].correspondent_profile
    assert bool(profile.contacted)
    assert isinstance(profile.contacted, datetime.datetime)
    for prop_name, _ in cached_property.get_cached_properties(profile):
        getattr(profile, prop_name)


@util.use_cassette
def test_looking_for_on_user_profile():
    profile = User().profile
    min, max = profile.looking_for.ages
    assert isinstance(profile.looking_for.single, bool)
    assert isinstance(profile.looking_for.near_me, bool)
    assert isinstance(profile.looking_for.kinds, list)


@util.use_cassette
def test_looking_for_write_on_user_profile(vcr_live_sleep):
    profile = User().profile
    new_single = not profile.looking_for.single
    new_ages_min, new_ages_max = profile.looking_for.ages
    new_ages_min += 1
    new_ages_max += 1
    new_near_me = not profile.looking_for.near_me
    new_kinds = (['long-term dating', 'casual sex']
                 if 'short-term dating' in profile.looking_for.kinds
                 else ['short-term dating', 'casual sex'])
    new_gentation = ('bi girls only' if 'everybody' in profile.looking_for.gentation
                     else 'everybody')

    sleep_time = 4
    profile.looking_for.ages = new_ages_min, new_ages_max
    vcr_live_sleep(sleep_time)
    profile.looking_for.near_me = new_near_me
    vcr_live_sleep(sleep_time)
    profile.looking_for.kinds = new_kinds
    vcr_live_sleep(sleep_time)
    profile.looking_for.gentation = new_gentation
    vcr_live_sleep(sleep_time)
    profile.looking_for.single = new_single

    vcr_live_sleep(sleep_time)
    new_profile = profile._session.get_profile(profile.username)
    assert new_profile.looking_for.single == new_single
    assert new_profile.looking_for.near_me == new_near_me
    assert new_profile.looking_for.ages == looking_for.LookingFor.Ages(new_ages_min,
                                                                       new_ages_max)
    assert set(new_profile.looking_for.kinds) == set(new_kinds)
    assert new_profile.looking_for.gentation == new_gentation


    assert profile.looking_for.single == new_single
    assert profile.looking_for.near_me == new_near_me
    assert profile.looking_for.ages == looking_for.LookingFor.Ages(new_ages_min,
                                                                   new_ages_max)
    assert set(profile.looking_for.kinds) == set(new_kinds)
    assert profile.looking_for.gentation == new_gentation


@util.use_cassette
def test_profile_with_unicode_characters():
    User().get_profile(u'Dimmahlé').age
