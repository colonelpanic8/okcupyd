# -*- coding: utf-8 -*-
import pytest

from okcupyd import settings
from okcupyd.session import Session
from okcupyd.errors import AuthenticationError
from . import util


@util.use_cassette(path='session_success')
def test_session_success():
    Session.login()


@util.use_cassette(path='session_failure')
def test_session_auth_failure():
    with pytest.raises(AuthenticationError):
        Session.login(password='wrong_password')


@util.use_cassette
def test_session_unicode():
    Session.login(username='éÅunicodeË', password='unicode')
