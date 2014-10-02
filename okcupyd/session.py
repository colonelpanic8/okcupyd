import logging

import requests

from .errors import AuthenticationError
from . import settings
from . import util
from . import profile


log = logging.getLogger(__name__)


class Session(requests.Session):

    default_login_headers = {
        'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/37.0.2062.94 '
                       'Safari/537.36')
    }

    @classmethod
    def login(cls, username=None, password=None):
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
        login_response = session.okc_post('login',
                                          data=credentials,
                                          headers=cls.default_login_headers,
                                          secure=True)
        log_in_name = login_response.json()['screenname']
        if log_in_name is None:
            raise AuthenticationError('Could not log in as {0}'.format(username))
        if log_in_name.lower() != username.lower():
            log.warning('Expected to log in as {0} but '
                        'got {1}'.format(username, log_in_name))
        log.debug(login_response.content.decode('utf8'))
        session.log_in_name = log_in_name
        session.headers.update(cls.default_login_headers)
        return session

    def get(self, *args, **kwargs):
        response = super(Session, self).get(*args, **kwargs)
        response.raise_for_status()
        return response

    def post(self, *args, **kwargs):
        response = super(Session, self).post(*args, **kwargs)
        response.raise_for_status()
        return response

    def okc_get(self, path, secure=None, **kwargs):
        response = self.get(self.build_path(path, secure), **kwargs)
        response.raise_for_status()
        return response

    def okc_post(self, path, secure=None, **kwargs):
        return self.post(self.build_path(path, secure), **kwargs)

    def build_path(self, path, secure=None):
        if secure is None:
            secure = 'secure_login' in self.cookies and int(self.cookies['secure_login']) != 0
        return u'{0}://{1}/{2}'.format('https' if secure else 'http',
                                     util.DOMAIN, path)

    def get_profile(self, username):
        return profile.Profile(self, username)

    def get_current_user_profile(self):
        return self.get_profile(self.log_in_name)
