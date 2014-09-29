import mock
import pytest

from okcupyd.search import SearchManager, SearchParameterBuilder, search
from okcupyd.profile import Profile
from . import util



@pytest.fixture
@util.use_cassette(cassette_name='search_startup')
def search_manager():
    return SearchManager(looking_for='everybody')

@util.use_cassette(cassette_name='search_age_filter')
def test_age_filter(search_manager):
    age = 22
    search_manager.set_options(age_min=age, age_max=age)
    profile, = search_manager.get_profiles(count=1)
    assert profile.age == age

@util.use_cassette(cassette_name='search_count')
def test_count_variable(search_manager, request):
    search_manager.set_options(looking_for='everybody')
    profiles = search_manager.get_profiles(count=14)
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
def test_location_filter(search_manager):
    location = 'Portland, OR'
    search_manager.set_options(location=location, radius=25)
    profile, = search_manager.get_profiles(count=1)
    assert profile.location == 'Portland, OR'

@util.use_cassette(cassette_name='search_function')
def test_search_function(session):
    profile, = search(session, count=1)
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
def test_search_manager_iter():
    search_manager = SearchManager(looking_for='everybody',
                                   religion='buddhist', age_min=25, age_max=25,
                                   location='new york, ny', keywords='bicycle')
    for profile in search_manager:
        assert isinstance(profile, Profile)


@mock.patch('okcupyd.helpers.get_locid', return_value=2)
def test_construction_of_all_search_parameters(mock_get_locid):
    spb = SearchParameterBuilder()
    spb.set_options(location='new york, ny', religion='buddhist',
                    height_min=66, height_max=68, looking_for='everybody',
                    smokes=['no', 'trying to quit'], age_min=18, age_max=24,
                    radius=12, order_by='MATCH', last_online=1234125,
                    status='single', drugs=['very_often', 'sometimes'],
                    job=['retired'], education=['high school'],
                    income='less than $20,000', monogomy='monogamous',
                    diet='vegan', ethnicity=['asian', 'middle eastern'],
                    pets=['owns dogs', 'likes cats'], kids=['has a kid'])
    spb.build(mock.Mock(), count=10)


def test_empty_string_looking_for():
    SearchParameterBuilder(looking_for='').build(mock.Mock())
