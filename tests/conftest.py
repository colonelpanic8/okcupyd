import os

import mock
import contextlib2 as contextlib
import pytest
from vcr.cassette import Cassette, CassetteContextDecorator

from . import util
from okcupyd import settings
from okcupyd import util as okcupyd_util
from okcupyd.session import Session


def pytest_addoption(parser):
    okcupyd_util.add_command_line_options(parser.addoption, use_short_options=False)
    parser.addoption('--live', dest='skip_vcrpy', action='store_true', default=False,
                     help="Skip the patching of http requests in tests. "
                     "USE WITH CAUTION. This will interact with the okcupid "
                     "website and send messages with any provided user credentials.")
    parser.addoption('--scrub', dest='scrub', action='store_true', default=False,
                     help="USE WITH CAUTION. Don't scrub PII from "
                     "http requests/responses. This is useful for recording cassetes.")
    parser.addoption('--resave', dest='resave',
                     action='store_true', default=False,
                     help="Resave cassettes. Use to retoractively scrub cassettes.")
    parser.addoption('--cassette-mode', dest='cassette_mode', action='store',
                     default='once', help="Accept new requests in all tests.")
    parser.addoption('--record', dest='record', action='store_true',
                     default=False, help="Re-record cassettes for all tests.")


def patch(option, *patches, **kwargs):
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


patch_settings = patch('credentials_modules',
                       mock.patch.object(settings, 'USERNAME', 'username'),
                       mock.patch.object(settings, 'PASSWORD', 'password'),
                       mock.patch.object(settings, 'AF_USERNAME', 'username'),
                       mock.patch.object(settings, 'AF_PASSWORD', 'password'),
                       mock.patch.object(settings, 'DELAY', 0), negate=True)
patch_save = patch('resave',
                   mock.patch.object(
                       Cassette, '_save',
                       okcupyd_util.n_partialable(Cassette._save)(force=True)))
patch_use_cassette_enabled = patch('skip_vcrpy',
                                   mock.patch.object(CassetteContextDecorator,
                                                     '__enter__'),
                                   mock.patch.object(CassetteContextDecorator,
                                                     '__exit__'))
patch_vcrpy_filters = patch('scrub',
                            mock.patch.object(util, 'SHOULD_SCRUB', False),
                            negate=True)

original_cassette_enter = CassetteContextDecorator.__enter__
def new_cassette_enter(self):
    path, _ = self._args_getter()
    try:
        os.remove(path)
    except:
        pass
    original_cassette_enter(self)
patch_record = patch('record', mock.patch.object(CassetteContextDecorator,
                                                 '__enter__',
                                                 new_cassette_enter))


@pytest.fixture(autouse=True, scope='session')
def set_vcr_options(request):
    util.okcupyd_vcr.record_mode = request.config.getoption('cassette_mode')


@pytest.fixture(autouse=True, scope='session')
def process_command_line_args(request):
    okcupyd_util.handle_command_line_options(request.config.option)


@pytest.fixture
def session():
    with util.use_cassette(cassette_name='session_success'):
        return Session.login()
