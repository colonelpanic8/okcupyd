import contextlib

import mock
import pytest
from vcr.cassette import CassetteContextDecorator, Cassette

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
    parser.addoption('--resave', dest='resave_cassettes',
                     action='store_true', default=False,
                     help="Resave cassettes. Use to retoractively scrub cassettes.")
    parser.addoption('--cassette-mode', dest='cassette_mode', action='store', default='once',
                    help="Accept new requests in all tests.")


def patch_when_option_set(option, *patches, **kwargs):
    negate = kwargs.get('negate', False)
    @pytest.yield_fixture(autouse=True, scope='session')
    def patch_conditionally(request):
        condition = bool(request.config.getoption(option))
        if negate: condition = not condition
        if condition:
            with contextlib.ExitStack() as exit_stack:
                for patch in patches:
                    exit_stack.enter_context(patch)
                yield
        else:
            yield
    return patch_conditionally


patch_settings = patch_when_option_set('credentials_modules',
                                       mock.patch.object(settings, 'USERNAME', 'username'),
                                       mock.patch.object(settings, 'PASSWORD', 'password'),
                                       mock.patch.object(settings, 'AF_USERNAME', 'username'),
                                       mock.patch.object(settings, 'AF_PASSWORD', 'password'),
                                       mock.patch.object(settings, 'DELAY', 0), negate=True)
patch_save = patch_when_option_set('resave_cassettes',
                                   mock.patch.object(
                                       Cassette, '_save',
                                       pyokc_util.n_partialable(Cassette._save)(force=True)))
# patch_use_cassette_enabled = patch_when_option_set('skip_vcrpy',
#                                                    mock.patch.object(CassetteContextDecorator,
#                                                                      '__enter__'),
#                                                    mock.patch.object(CassetteContextDecorator,
#                                                                      '__exit__'))
patch_vcrpy_filters = patch_when_option_set('scrub',
                                            mock.patch.object(util, 'SHOULD_SCRUB', False),
                                            negate=True)


@pytest.fixture(autouse=True, scope='session')
def set_vcr_options(request):
    util.pyokc_vcr.record_mode = request.config.getoption('cassette_mode')


@pytest.yield_fixture(autouse=True, scope='session')
def process_command_line_args(request):
    pyokc_util.handle_command_line_options(request.config.option)
    if request.config.getoption('skip_vcrpy') or request.config.getoption('credentials_modules'):
        with mock.patch.object(util, 'TESTING_USERNAME', settings.USERNAME):
            yield
    else:
        yield


@pytest.fixture
def session():
    with util.use_cassette('session_success'):
        return Session.login()
