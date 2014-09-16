import time
import logging

import requests

from .errors import AuthenticationError
from . import settings


log = logging.getLogger(__name__)


class Session(requests.Session):

    default_login_headers = {
        'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/37.0.2062.94 '
                       'Safari/537.36')
    }

    @classmethod
    def login(cls, username=settings.USERNAME, password=settings.PASSWORD, headers=None):
        session = cls()
        credentials = {
            'username': username,
            'password': password,
            'okc_api': 1
        }
        login_response = session.post('https://www.okcupid.com/login',
                                      data=credentials,
                                      headers=headers or cls.default_login_headers)
        if login_response.json()['screenname'] is None or  (
            login_response.json()['screenname'].lower() != username.lower()
        ):
            raise AuthenticationError('Could not log in with the credentials provided')
        return session

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp = -settings.DELAY

    def _throttle(self):
        while time.clock() - self.timestamp < settings.DELAY:
            time.sleep(.5)
        self.timestamp = time.clock()

    def post(self, *args, **kwargs):
        self._throttle()
        response = super().post(*args, **kwargs)
        response.raise_for_status()
        return response

    def get(self, *args, **kwargs):
        self._throttle()
        response = super().get(*args, **kwargs)
        response.raise_for_status()
        return response
