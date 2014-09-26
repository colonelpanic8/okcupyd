import pytest

from okcupyd import settings
from okcupyd.session import Session
from okcupyd.errors import AuthenticationError
from . import util


@util.use_cassette(cassette_name='session_success')
def test_session_success():
    Session.login()


@util.use_cassette(cassette_name='session_failure')
def test_session_auth_failure():
    with pytest.raises(AuthenticationError):
        Session.login(password='wrong_password')
