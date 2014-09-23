import time
import logging

import requests

from . import helpers
from .settings import DELAY, USERNAME, PASSWORD


log = logging.getLogger(__name__)


class Session(requests.Session):

    @classmethod
    def login(cls, username=USERNAME, password=PASSWORD, headers=None):
        session = cls()
        helpers.login(session, {'username': username,
                                 'password': password}, headers)
        return session

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp = -DELAY

    def _throttle(self):
        while time.clock() - self.timestamp < DELAY:
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
