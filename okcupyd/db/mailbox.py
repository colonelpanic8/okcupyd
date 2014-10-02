import logging

import simplejson

from okcupyd import helpers
from okcupyd.db import adapters
from okcupyd.db import model, txn


log = logging.getLogger(__name__)


class Sync(object):

    def __init__(self, user):
        self._user = user

    def all(self):
        with txn() as session:
            okcupyd_user = session.query(model.OKCupydUser).join(model.User).filter(
                model.User.okc_id == self._user.profile.id
            ).with_for_update().one()

            log.info(simplejson.dumps({
                'outbox_last_updated': helpers.datetime_to_string(
                    okcupyd_user.outbox_last_updated
                ),
                'inbox_last_updated': helpers.datetime_to_string(
                    okcupyd_user.inbox_last_updated
                )
            }))

            okcupyd_user.outbox_last_updated = self._sync_mailbox_until(
                self._user.outbox(),
                okcupyd_user.outbox_last_updated
            )
            okcupyd_user.inbox_last_updated = self._sync_mailbox_until(
                self._user.inbox(),
                okcupyd_user.inbox_last_updated
            )

    def _sync_mailbox_until(self, mailbox, sync_until):
        for thread in mailbox:
            if sync_until and sync_until > thread.datetime:
                break
            if not thread.messages:
                continue
            if not thread.with_deleted_user:
                adapters.ThreadAdapter(thread).get_thread()
        try:
            return mailbox[0].datetime
        except IndexError:
            pass
