import pytest

from pyokc.search import Search
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
    def test_match_card_extractor(self, search):
        profiles = search.get_profiles(count=22)
        assert len(profiles) == 22

        first_profile = profiles[0]

        assert first_profile.username.lower() == 'BetterBeReal'.lower()
        assert first_profile.age == 50
        assert first_profile.location == 'Darby, MT'
        assert first_profile.match_percentage == 99
        assert first_profile.enemy_percentage == 3
        assert first_profile.id == '14907401137919384845'
        assert first_profile.contacted == False
        assert first_profile.rating == 0

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
