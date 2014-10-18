import datetime

import sqlalchemy

from okcupyd.db import mailbox, model, txn
import time


class MessageHandler(object):

    def __init__(self, user, *handlers):
        self.user = user
        self.handlers = handlers

    def handle_messages(self, sleep_time=30, sync_until=None):
        while True:
            _, new_messages = mailbox.Sync(self.user).inbox()
            with txn() as session:
                for message in new_messages:
                    session.add(message)
                for handler in self.handlers:
                    handler(self.user, new_messages)
            time.sleep(sleep_time)


def do_it():
    def handle(user, messages):
        if len(messages) == 0:
            return
        messages = messages[::-1]
        new_wall = u'\n'.join(
            u'<a href="http://www.okcupid.com/profile/{0}">{0}</a>: {1}\n'.format(
                message.sender.handle, message.text
            )
            for message in messages
            if message.sender.handle != 'pumpkinmania8'
        ) + user.profile.essays.my_life
        user.profile.essays.my_life = new_wall.replace('\n\n', '\n')

    import okcupyd
    MessageHandler(okcupyd.User.from_credentials('pumpkinmania8', 'thisisforokc'),
                   handle).handle_messages()
