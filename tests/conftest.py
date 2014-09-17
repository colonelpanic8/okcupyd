import mock
import pytest
from vcr.cassette import use_cassette

from . import util
from pyokc import settings
from pyokc import util as pyokc_util
from pyokc.session import Session


def pytest_addoption(parser):
    pyokc_util.add_command_line_options(parser.addoption, use_short_options=False)
    parser.addoption('--live', dest='skip_vcrpy', action='store_true', default=False,
                    help="Skip the patching of http requests in tests. "
                    "USE WITH CAUTION. This will interact with the okcupid "
                    "website and send messages with any provided user credentials.")
    parser.addoption('--no-scrub', dest='scrub', action='store_false', default=True,
                    help="USE WITH CAUTION. Don't scrub PII from "
                    "http requests/responses. This is useful for recording cassetes.")
    parser.addoption('--resave-cassettes', dest='resave_cassettes',
                     action='store_true', default=False,
                     help="Resave cassettes. Use to retoractively scrub cassettes.")



@pytest.yield_fixture(autouse=True, scope='session')
def patch_settings(request):
    if not request.config.getoption('credentials_modules'):
        with mock.patch.object(settings, 'USERNAME', 'username'), \
             mock.patch.object(settings, 'PASSWORD', 'password'), \
             mock.patch.object(settings, 'AF_USERNAME', 'username'), \
             mock.patch.object(settings, 'AF_PASSWORD', 'password'), \
             mock.patch.object(settings, 'DELAY', 0):
            yield
    else:
        yield


@pytest.yield_fixture(autouse=True, scope='session')
def patch_use_cassette_enabled(request):
    if request.config.getoption('skip_vcrpy'):
        with mock.patch.object(use_cassette, '_enabled', False):
            yield
    else:
        yield


@pytest.yield_fixture(autouse=True, scope='session')
def patch_vcrpy_filters(request):
    if request.config.getoption('scrub'):
        yield
    else:
        with mock.patch.object(util, 'SHOULD_SCRUB', False):
            yield


@pytest.fixture(autouse=True, scope='session')
def process_command_line_args(request):
    pyokc_util.handle_command_line_options(request.config.option)


@pytest.fixture
def session():
    with util.use_cassette('session_success'):
        return Session.login(username=settings.USERNAME, password=settings.PASSWORD)
