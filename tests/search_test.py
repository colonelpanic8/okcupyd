import mock
import pytest

from pyokc.search import SearchManager, SearchParameterBuilder, search
from pyokc.profile import Profile
from pyokc.session import Session
from . import util


class TestSearch(object):

    @pytest.fixture
    def search_manager(self, session):
        return SearchManager(Session(), looking_for='everybody')

    @util.use_cassette('search_age_filter')
    def test_age_filter(self, search_manager):
        age = 22
        search_manager.set_options(age_min=age, age_max=age)
        profile, = search_manager.get_profiles(count=1)
        assert profile.age == age

    @util.use_cassette('search')
    def test_match_card_extractor(self, search_manager, request):
        search_manager.set_options(keywords='hannahmv', looking_for='everybody')
        profiles = search_manager.get_profiles(count=1)
        assert len(profiles) == 1

        # TODO(IvanMalison): This is crap -- clean this up.
        first_profile = profiles[0]
        assert first_profile.username.lower() == 'hannahmv'.lower()
        assert first_profile.age == 27
        assert first_profile.location == 'Astoria, NY'
        assert isinstance(first_profile.match_percentage, int)
        assert isinstance(first_profile.enemy_percentage, int)
        assert first_profile.id == '10558689643648617771'
        assert first_profile.contacted == False
        assert first_profile.rating == 0

    @util.use_cassette('search_count')
    def test_count_variable(self, search_manager, request):
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

    @util.use_cassette('search_location_filter')
    def test_location_filter(self, search_manager):
        location = 'Portland, OR'
        search_manager.set_options(location=location, radius=25)
        profile, = search_manager.get_profiles(count=1)
        assert profile.location == 'Portland, OR'

    @util.use_cassette('search_function')
    def test_search_function(self, session):
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


@mock.patch('pyokc.helpers.get_locid', return_value=2)
def test_construction_of_all_search_parameters(mock_get_locid):
    spb = SearchParameterBuilder()
    spb.set_options(location='new york, ny', religion='buddhist',
                              height_min=66, height_max=68, looking_for='everybody',
                              smokes=['no', 'trying to quit'], age_min=18, age_max=24,
                              radius=12, order_by='MATCH', last_online=1234125,
                              status='single', drugs=['very_often', 'sometimes'],
                              job=['retired'], education=['high school'],
                              income='less than $20,000', monogomy='monogamous',
                              diet='vegan', ethnicity=['asian', 'middle eastern'])

    print(spb.build(mock.Mock(), count=10))
