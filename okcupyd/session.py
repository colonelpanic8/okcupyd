import time
import logging

import requests

from .errors import AuthenticationError
from . import settings
from . import util


log = logging.getLogger(__name__)


class Session(requests.Session):

    default_login_headers = {
        'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/37.0.2062.94 '
                       'Safari/537.36')
    }

    @classmethod
    def login(cls, username=None, password=None, headers=None):
        # settings.USERNAME and settings.PASSWORD should not be made
        # the defaults to their respective arguments because doing so
        # would prevent this function from picking up any changes made
        # to those values after import time.
        username = username or settings.USERNAME
        password = password or settings.PASSWORD
        session = cls()
        credentials = {
            'username': username,
            'password': password,
            'okc_api': 1
        }
        login_response = session.post('https://www.okcupid.com/login',
                                      data=credentials,
                                      headers=headers or cls.default_login_headers)
        log_in_name = login_response.json()['screenname']
        if log_in_name is None:
            raise AuthenticationError('Could not log in as {0}'.format(username))
        if log_in_name.lower() != username.lower():
            log.warning('Expected to log in as {0} but got {1}'.format(username,
                                                                       log_in_name))
        log.debug(login_response.content.decode('utf8'))
        session.log_in_name = log_in_name
        return session

    def __init__(self, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.timestamp = -settings.DELAY

    def _throttle(self):
        while time.clock() - self.timestamp < settings.DELAY:
            time.sleep(.5)
        self.timestamp = time.clock()

    def post(self, *args, **kwargs):
        self._throttle()
        response = super(Session, self).post(*args, **kwargs)
        response.raise_for_status()
        return response

    def get(self, *args, **kwargs):
        self._throttle()
        response = super(Session, self).get(*args, **kwargs)
        response.raise_for_status()
        return response

    def okc_get(self, path, *args, **kwargs):
        return self.get('{0}{1}'.format(util.BASE_URI, path), *args, **kwargs)

    def okc_post(self, path, *args, **kwargs):
        return self.post('{0}{1}'.format(util.BASE_URI, path), *args, **kwargs)