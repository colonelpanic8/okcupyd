from okcupyd.search import SearchFetchable, search
from okcupyd.profile import Profile
from . import util


@util.use_cassette(cassette_name='search_age_filter')
def test_age_filter():
    age = 22
    search_fetchable = SearchFetchable(looking_for='everybody',
                                       age_min=age, age_max=age)

    profile = next(iter(search_fetchable))
    assert profile.age == age


@util.use_cassette(cassette_name='search_count')
def test_count_variable(request):
    profiles = search(looking_for='everybody', count=14)
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
    search_fetchable = SearchFetchable(looking_for='everybody',
                                       religion='buddhist', age_min=25, age_max=25,
                                       location='new york, ny', keywords='bicycle')
    for count, profile in enumerate(search_fetchable):
        assert isinstance(profile, Profile)
        if count > 30:
            break
