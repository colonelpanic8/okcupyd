import pytest

from pyokc import settings
from pyokc.session import Session
from pyokc.errors import AuthenticationError
from . import util


@util.use_cassette('session_success')
def test_session_success():
    Session.login()


@util.use_cassette('session_failure')
def test_session_auth_failure():
    with pytest.raises(AuthenticationError):
        Session.login(password='wrong_password')
