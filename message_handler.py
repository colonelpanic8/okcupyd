from pytz import timezone

from okcupyd.db import mailbox, model, txn
import time


class MessageHandler(object):

    def __init__(self, user, *handlers):
        self.user = user
        self.handlers = handlers

    def handle_messages(self, sleep_time=30, sync_until=None):
        while True:
            _, new_messages = mailbox.Sync(self.user).inbox()
            for handler in self.handlers:
                handler(self.user, new_messages)
            time.sleep(sleep_time)

WALL_SIZE = 35000
def handle(user, messages):
    if len(messages) == 0:
        return
    messages = messages[::-1]
    messages = [message for message in messages
                if message.sender.handle.lower() != user.username.lower()]


    message_groups = []
    current = []
    projected_length = 0

    my_timezone=timezone('US/Pacific')
    for message in messages:
        timestamp = my_timezone.localize(message.created_at)
        new_message = u'{0} <a href="http://www.okcupid.com/profile/{1}">{1}</a>: {2}'.format(
            timestamp.strftime('%I:%M'), message.sender.handle, message.text
        )
        message_length = len(new_message) + 2
        projected_length += message_length
        if projected_length > WALL_SIZE:
            message_groups.append(current)
            projected_length = message_length
            current = [new_message]
        else:
            current.append(new_message)

    for message_group, essay_name in zip(message_groups, user.profile.essays.essay_names[1:]):
        setattr(user.profile.essays, essay_name, '\n\n'.join(message_group))

def reset(user, ignore):
    with txn() as session:
        messages = model.Message.query_no_txn(session)
        handle(user, sorted(messages, key=lambda m: m.created_at))

def do_it():
    import okcupyd
    MessageHandler(okcupyd.User.from_credentials('pumpkinmania8', 'thisisforokc'),
                   reset).handle_messages(sleep_time=20)
