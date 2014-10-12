import pytest

from okcupyd.magicnumbers import maps
from okcupyd.session import Session
from okcupyd.search import SearchFetchable, search
from okcupyd.profile import Profile

from . import util


@util.use_cassette(cassette_name='search_age_filter')
def test_age_filter():
    age = 22
    search_fetchable = SearchFetchable(gentation='everybody',
                                       age_min=age, age_max=age)

    profile = next(iter(search_fetchable))
    assert profile.age == age


@util.use_cassette(cassette_name='search_count')
def test_count_variable(request):
    profiles = search(gentation='everybody', count=14)
    assert len(profiles) == 14

    for profile in profiles:
        profile.username
        profile.age
        profile.location
        profile.match_percentage
        profile.enemy_percentage
        profile.id
        profile.rating
        profile.contacted


@util.use_cassette(cassette_name='search_location_filter')
def test_location_filter():
    location = 'Portland, OR'
    search_fetchable = SearchFetchable(location=location, radius=25)
    profile = search_fetchable[0]
    assert profile.location == 'Portland, OR'


@util.use_cassette(cassette_name='search_function')
def test_search_function():
    profile, = search(count=1)
    assert isinstance(profile, Profile)

    profile.username
    profile.age
    profile.location
    profile.match_percentage
    profile.enemy_percentage
    profile.id
    profile.rating
    profile.contacted


@util.use_cassette
def test_search_fetchable_iter():
    search_fetchable = SearchFetchable(gentation='everybody',
                                       religion='buddhist', age_min=25, age_max=25,
                                       location='new york, ny', keywords='bicycle')
    for count, profile in enumerate(search_fetchable):
        assert isinstance(profile, Profile)
        if count > 30:
            break


@pytest.mark.xfail
@util.use_cassette
def test_easy_search_filters():
    session = Session.login()
    query_test_pairs = [#('bodytype', maps.bodytype), # Why doesn't this work?
                        ('drugs', maps.drugs), ('smokes', maps.smokes),
                        ('diet', maps.diet,), ('job', maps.job)]
    for query_param, re_map in query_test_pairs:
        for value in re_map.pattern_to_value.keys():
            profile = SearchFetchable(**{
                'gentation': '',
                'session': session,
                'count': 1,
                query_param: value
            })[0]
            attribute = getattr(profile.details, query_param)
            assert value in (attribute or '').lower()


@pytest.mark.xfail
@util.use_cassette
def test_children_filter():
    session = Session.login()
    profile = SearchFetchable(session, wants_kids="wants kids", count=1)[0]
    assert "wants kids" in profile.details.children.lower()

    profile = SearchFetchable(session, has_kids=["has kids"],
                              wants_kids="doesn't want kids",
                              count=0)[0]
    assert "has kids" in profile.details.children.lower()
    assert "doesn't want kids" in profile.details.children.lower()


@util.use_cassette
def test_pets_queries():
    session = Session.login()
    profile = SearchFetchable(session, cats=['dislikes cats', 'likes cats'],
                              count=1)[0]
    assert 'likes cats' in profile.details.pets.lower()

    profile = SearchFetchable(session, dogs='likes dogs', count=1)[0]

    assert 'likes dogs' in profile.details.pets.lower()
