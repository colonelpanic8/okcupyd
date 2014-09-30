from okcupyd.db import adapters


class MailboxSyncer(object):

    def __init__(self, mailbox):
        self._mailbox = mailbox

    def sync(self):
        threads = self._mailbox.refresh()
        for thread in threads:
            adapters.ThreadAdapter(thread).get_thread()
