import datetime

from . import util
from okcupyd import profile
from okcupyd import session
from okcupyd import User
from okcupyd.util import cached_property


@util.use_cassette(cassette_name='test_profile_essays')
def test_profile_essays():
    user_profile = profile.Profile(session.Session.login(), 'FriedLiverAttack')
    assert user_profile.essays.self_summary


@util.use_cassette(cassette_name='test_rate_profile')
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


@util.use_cassette(cassette_name='test_profile_contacted')
def test_contacted():
    profile = User().quickmatch()
    profile.message('test')
    assert bool(profile.contacted)
    assert isinstance(profile.contacted, datetime.datetime)


@util.use_cassette(cassette_name='test_profile_on_inbox_correspondent')
def test_contacted_on_inbox_correspondent():
    profile = User().outbox[-1].correspondent_profile
    assert bool(profile.contacted)
    assert isinstance(profile.contacted, datetime.datetime)
    for prop_name, _ in cached_property.get_cached_properties(profile):
        getattr(profile, prop_name)
