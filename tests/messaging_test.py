import pytest

from pyokc import messaging
from pyokc import objects


class TestMailboxFetcher(object):

    @pytest.fixture
    def session(self):
        return objects.Session.login()

    @pytest.fixture(params=[1, 2, 4])
    def mailbox_fetcher(self, session, request):
        return messaging.MailboxFetcher(session, request.param)

    def test_process_message_element_inbox(self, mailbox_fetcher):
        message_threads = mailbox_fetcher.get_threads()
        for message_thread in message_threads:
            assert message_thread.correspondent != None
