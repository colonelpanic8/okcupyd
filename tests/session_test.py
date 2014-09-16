import pytest

from pyokc.session import Session
from pyokc.errors import AuthenticationError
from . import util


@util.use_cassette('session_success')
def test_session_success():
    Session.login(username='username', password='password')


@util.use_cassette('session_failure')
def test_session_failure():
    with pytest.raises(AuthenticationError):
        Session.login(username=None, password=None)


@util.use_cassette('session_auth_failure')
def test_session_auth_failure():
    with pytest.raises(AuthenticationError):
        Session.login(username='username', password='password')
