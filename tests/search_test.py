import pytest

from pyokc.search import Search, search
from pyokc.profile import Profile
from . import util


class TestSearch(object):

    @pytest.fixture
    def search(self, session):
        return Search(session)

    @util.use_cassette('search_age_filter')
    def test_age_filter(self, search):
        age = 22
        search.set_options(age_min=age, age_max=age)
        profile, = search.get_profiles(count=1)
        assert profile.age == age

    @util.use_cassette('search')
    def test_match_card_extractor(self, search, request):
        search.set_options(keywords='hannahmv', looking_for='everybody')
        profiles = search.get_profiles(count=1)
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
    def test_count_variable(self, search, request):
        search.set_options(looking_for='everybody')
        profiles = search.get_profiles(count=14)
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
    def test_location_filter(self, search):
        location = 'Portland, OR'
        search.set_options(location=location, radius=25)
        profile, = search.get_profiles(count=1)
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
