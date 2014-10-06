import datetime

import pytest

from . import util
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
    # TODO: get rid of circular import so you can do this.
    profile = User().quickmatch()
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


@pytest.mark.xfail
def test_looking_for_write_on_user_profile():
    new_single = not profile.looking_for.single
    new_ages_min, new_ages_max = profile.looking_for.ages
    new_ages_min += 1
    new_ages_max += 1
    new_near_me = not profile.looking_for.near_me
    new_relationships = ['short_term']
    new_gentation = []

    profile.looking_for.ages = new_ages_min, new_ages_max
    profile.looking_for.single = new_single
    profile.looking_for.near_me = new_near_me
    profile.looking_for.relationships = new_relationships
    profile.looking_for.gentation = new_gentation

    assert profile.looking_for.single == new_single
    assert profile.relationships == new_gentation
    assert profile.looking_for.ages == profile.LookingFor.ages(new_ages_min,
                                                               new_ages_max)


@util.use_cassette
def test_details():
    pass
