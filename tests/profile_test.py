import pytest

from okcupyd import profile
from okcupyd import session


def test_profile_essays():
    user_profile = profile.Profile(session.Session.login(), 'FriedLiverAttack')
    assert user_profile.essays.self_summary

    with pytest.raises(profile.CantUpdateOtherUsersEssaysError):
        user_profile.self_summary = 'test'
