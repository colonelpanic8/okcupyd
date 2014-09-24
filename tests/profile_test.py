import pytest

from . import util
from okcupyd import profile
from okcupyd import session


@util.use_cassette('test_profile_essays')
def test_profile_essays():
    user_profile = profile.Profile(session.Session.login(), 'FriedLiverAttack')
    assert user_profile.essays.self_summary

    with pytest.raises(profile.CantUpdateOtherUsersEssaysError):
        user_profile.essays.self_summary = 'test'
