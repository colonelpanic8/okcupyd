import pytest

from pyokc import messaging

from .conftest import build_mock_session


class TestMailboxFetcher(object):

    @pytest.fixture
    def mock_session(self):
        return build_mock_session()

    @pytest.fixture(params=[1, 2, 4])
    def mailbox_fetcher(self, mock_session, request):
        return messaging.MailboxFetcher(mock_session, request.param)

    def test_process_message_element_inbox(self, mailbox_fetcher):
        message_threads = mailbox_fetcher.get_threads()
        for message_thread in message_threads:
            assert message_thread.correspondent != None
