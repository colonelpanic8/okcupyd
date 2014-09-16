import mock
import pytest

from . import util
from pyokc import settings
from pyokc.session import Session


def pytest_addoption(parser):
    parser.addoption("--enable-logger", dest='enabled_logs', action="append", default=[],
                     help="Enable and add a handler for the specified logger.")


@pytest.yield_fixture(autouse=True, scope='session')
def patch_settings():
    with mock.patch.object(settings, 'USERNAME', 'username'), \
         mock.patch.object(settings, 'PASSWORD', 'password'), \
         mock.patch.object(settings, 'AF_USERNAME', 'username'), \
         mock.patch.object(settings, 'AF_PASSWORD', 'password'), \
         mock.patch.object(settings, 'DELAY', 0):
        yield


@pytest.fixture(autouse=True, scope='session')
def setup_logs(request):
    for log in request.config.getoption('enabled_logs'):
        util.enable_log(log)


@pytest.fixture
def session():
    with util.use_cassette('session_success'):
        return Session.login(username='username', password='password')
