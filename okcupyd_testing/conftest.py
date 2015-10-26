import datetime
import logging
import itertools
import time

import mock
import contextlib2 as contextlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vcr.cassette import Cassette, CassetteContextDecorator

from . import util
from okcupyd import db, settings
from okcupyd import util as okcupyd_util
from okcupyd.db import model, adapters


log = logging.getLogger(__name__)
BREAK_ON_EXCEPTION = False


def pytest_addoption(parser):
    okcupyd_util.add_command_line_options(
        parser.addoption, use_short_options=False
    )
    parser.addoption('--live', dest='skip_vcrpy', action='store_true',
                     default=False, help="Skip the patching of http requests in"
                     " tests. USE WITH CAUTION. This will interact with the "
                     "okcupid website and send messages with any provided user "
                     "credentials.")
    parser.addoption('--scrub', dest='scrub', action='store_true',
                     help="Scrub PII from http requests/responses. "
                     "This is useful for recording cassetes.", default=False)
    parser.addoption('--resave', dest='resave',
                     action='store_true', default=False,
                     help="Resave cassettes. Use to retoractively scrub "
                     "cassettes.")
    parser.addoption('--cassette-mode', dest='cassette_mode', action='store',
                     default='once', help="Accept new requests in all tests.")
    parser.addoption('--record', dest='record', action='store_true',
                     default=False, help="Re-record cassettes for all tests.")
    parser.addoption('--break-exc', dest='break_on_exception',
                     default=False, action='store_true', help="Enter ipdb if an"
                     " exception is encountered in a test.")


def patch(option, *patches, **kwargs):
    negate = kwargs.get('negate', False)

    @pytest.yield_fixture(autouse=True, scope='session')
    def patch_conditionally(request):
        condition = bool(request.config.getoption(option))
        if negate:
            condition = not condition
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
                       negate=True)


patch_save = patch(
    'resave', mock.patch.object(
        Cassette, '_save', okcupyd_util.curry(Cassette._save)(force=True)
    )
)


def reraise_exception(obj, error_type, error, traceback):
    if error is not None:
        raise


patch_use_cassette_enabled = patch(
    'skip_vcrpy',
    mock.patch.object(CassetteContextDecorator, '__enter__',
                      lambda stuff: log.debug("Skipping vcrpy patching.")),
    mock.patch.object(CassetteContextDecorator, '__exit__',
                      reraise_exception)
)

patch_vcrpy_filters = patch(
    'scrub', mock.patch.object(util, 'SHOULD_SCRUB', True)
)

patch_break_on_exception = patch(
    'break_on_exception',
    mock.patch('okcupyd_testing.conftest.BREAK_ON_EXCEPTION', True)
)

original_load = Cassette._load


def new_load(self):
    self.dirty = False
    self.rewound = True


patch_record = patch(
    'record', mock.patch.object(
        Cassette, '_load', new_load
    )
)


@pytest.fixture(autouse=True, scope='session')
def set_vcr_options(request):
    util.okcupyd_vcr.record_mode = request.config.getoption('cassette_mode')


@pytest.fixture(autouse=True, scope='session')
def process_command_line_args(request):
    okcupyd_util.handle_command_line_options(request.config.option)


@pytest.fixture(scope='function')
def engine(request):
    return create_engine('sqlite://', echo=request.config.getoption('echo'))


@pytest.fixture(scope='function')
def session(engine):
    new_kwargs = db.Session.kw.copy()
    new_kwargs['bind'] = engine
    return sessionmaker(**new_kwargs)


@pytest.yield_fixture(autouse=True, scope='function')
def setup_db(engine, session):
    with mock.patch.object(db, 'Session', session):
        orig_engine = db.Base.metadata.bind
        db.Base.metadata.bind = engine
        db.Base.metadata.drop_all()
        db.Base.metadata.create_all()
        yield
        db.Base.metadata.bind = orig_engine


@pytest.fixture
def T(mock_profile_builder, mock_message_thread_builder, mock_message_builder):

    class testing(object):
        pass

    testing.ensure = mock.Mock()
    testing.build_mock = mock.Mock()
    testing.factory = mock.Mock()

    def ensure_thread_model_resembles_okcupyd_thread(
        thread_model, okcupyd_thread
    ):
        assert thread_model.okc_id == okcupyd_thread.id
        ensure_user_model_resembles_okcupyd_profile(
            thread_model.initiator, okcupyd_thread.initiator
        )
        ensure_user_model_resembles_okcupyd_profile(
            thread_model.respondent, okcupyd_thread.respondent
        )
        for pair in zip(thread_model.messages, okcupyd_thread.messages):
            ensure_message_model_resembles_okcupyd_message(*pair)
            assert len(thread_model.messages) == len(okcupyd_thread.messages)

    def ensure_message_model_resembles_okcupyd_message(
        message_model, okcupyd_message
    ):
        assert message_model.okc_id == okcupyd_message.id
        assert message_model.sender.handle == okcupyd_message.sender.username
        assert message_model.recipient.handle == okcupyd_message.recipient.username
        assert message_model.text == okcupyd_message.content

    def ensure_user_model_resembles_okcupyd_profile(user_model,
                                                    okcupyd_profile):
        assert user_model.handle == okcupyd_profile.username

    testing.ensure.user_model_resembles_okcupyd_profile = \
        ensure_user_model_resembles_okcupyd_profile
    testing.ensure.message_model_resembles_okcupyd_message = \
        ensure_message_model_resembles_okcupyd_message
    testing.ensure.thread_model_resembles_okcupyd_thread = \
        ensure_thread_model_resembles_okcupyd_thread

    testing.build_mock.thread = mock_message_thread_builder
    testing.build_mock.message = mock_message_builder
    testing.build_mock.profile = mock_profile_builder

    def build_message_thread():
        message_thread = testing.build_mock.thread()
        return adapters.ThreadAdapter(message_thread).get_thread()[0]

    def build_user(username):
        profile = testing.build_mock.profile(username)
        return adapters.UserAdapter(profile).get()

    def build_okcupyd_user(user):
        user_model = model.User.from_profile(user.profile)
        user_model.upsert_model(id_key='okc_id')
        okcupyd_user = model.OKCupydUser(user_id=user_model.id)
        okcupyd_user.upsert_model(id_key='user_id')
        return okcupyd_user

    testing.factory.message_thread = build_message_thread
    testing.factory.user = build_user
    testing.factory.okcupyd_user = build_okcupyd_user
    return testing


@pytest.fixture
def mock_profile_builder():
    counter = itertools.count()
    next(counter)
    username_to_profile = {}

    def _build_mock_profile(username='username', age=30, id=None,
                            location='San Francisco, CA', **kwargs):
        if username in username_to_profile:
            return username_to_profile[username]
        if id is None:
            id = next(counter)
        mock_profile = mock.MagicMock(id=id or next(counter), location=location,
                                      age=age, username=username, **kwargs)
        username_to_profile[username] = mock_profile
        return mock_profile

    return _build_mock_profile


@pytest.fixture
def mock_message_builder():
    counter = itertools.count()
    next(counter)

    def _build_mock_message(id=None, sender='sender', recipient='recipient',
                            content='content', **kwargs):
        kwargs.setdefault('time_sent',
                          datetime.datetime(year=2014, day=2, month=4))
        if id is None:
            id = next(counter)
        assert isinstance(sender, str)
        assert isinstance(recipient, str)
        return mock.MagicMock(id=id, sender=mock.Mock(username=sender),
                              recipient=mock.Mock(username=recipient),
                              content=content, **kwargs)

    return _build_mock_message


@pytest.fixture
def mock_message_thread_builder(mock_message_builder, mock_profile_builder):
    counter = itertools.count()
    next(counter)

    def _build_mock_message_thread(id=None, message_count=2,
                                   initiator='initiator',
                                   respondent='respondent', **kwargs):
        if id is None:
            id = next(counter)
        messages = [mock_message_builder(content='{0}'.format(i),
                                         sender=respondent
                                         if i % 2 else initiator,
                                         recipient=initiator
                                         if i % 2 else respondent)
                    for i in range(message_count)]
        kwargs.setdefault('datetime',
                          datetime.datetime(year=2014, day=2, month=4))
        message_thread = mock.MagicMock(id=id, messages=messages, **kwargs)
        message_thread.initiator = mock_profile_builder(initiator)
        message_thread.respondent = mock_profile_builder(respondent)
        return message_thread
    return _build_mock_message_thread


def pytest_exception_interact():
    if BREAK_ON_EXCEPTION:
        import ipdb; ipdb.set_trace()
    try:
        models = []
        for key in dir(model):
            prospect = getattr(model, key)
            if isinstance(prospect, type) and issubclass(prospect, db.Base):
                models.append(prospect)
        model_class_to_instances = {}
        for model_class in models:
            model_class_to_instances[model_class] = {
                instance.okc_id: instance for instance in model_class.query()
            }
        log.info(model_class_to_instances)
    except:
        pass


@pytest.fixture
def vcr_live_sleep(request):
    return (time.sleep
            if (request.config.getoption('record') or
                request.config.getoption('skip_vcrpy'))
            else mock.Mock())
