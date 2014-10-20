import logging

import simplejson

from okcupyd import helpers
from okcupyd.db import adapters
from okcupyd.db import model, txn
from okcupyd.util import curry


log = logging.getLogger(__name__)


class Sync(object):
    """Sync messages from a users inbox to the okc database."""

    def __init__(self, user):
        self._user = user

    def all(self):
        self.update_mailbox('outbox')
        return self.update_mailbox('inbox')

    @curry
    def update_mailbox(self, mailbox_name='inbox'):
        """Update the mailbox associated with the given mailbox name.
        """
        with txn() as session:
            last_updated_name = '{0}_last_updated'.format(mailbox_name)
            okcupyd_user = session.query(model.OKCupydUser).join(model.User).filter(
                model.User.okc_id == self._user.profile.id
            ).with_for_update().one()
            log.info(simplejson.dumps({
                '{0}_last_updated'.format(mailbox_name): helpers.datetime_to_string(
                    getattr(okcupyd_user, last_updated_name)
                )
            }))

            res = self._sync_mailbox_until(
                getattr(self._user, mailbox_name)(),
                getattr(okcupyd_user, last_updated_name)
            )
            if not res:
                return None, None

            last_updated, threads, new_messages = res
            if last_updated:
                setattr(okcupyd_user, last_updated_name, last_updated)
            return threads, new_messages

    inbox = update_mailbox(mailbox_name='inbox')
    outbox = update_mailbox(mailbox_name='outbox')

    def _sync_mailbox_until(self, mailbox, sync_until):
        threads = []
        messages = []
        for thread in mailbox:
            if sync_until and sync_until > thread.datetime:
                break
            if not thread.messages:
                continue
            if not thread.with_deleted_user:
                thread, new_messages = adapters.ThreadAdapter(thread).get_thread()
                threads.append(threads)
                messages.extend(new_messages)
        try:
            return mailbox[0].datetime, threads, messages
        except IndexError:
            pass
