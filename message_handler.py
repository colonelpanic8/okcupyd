import re

from pytz import timezone
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
            mailbox.Sync(self.user).outbox()
            for handler in self.handlers:
                handler(self.user, new_messages)
            time.sleep(sleep_time)


send_re = re.compile('(.*?): (.*)')
def get_stuff(message_text):
    match = send_re.match(message_text)
    return match.group(1), match.group(2)


def let_other_users_respond(*users):
    def handle(user, new_messages):
        for new_message in new_messages:
            if new_message.sender.handle.lower() in users:
                try:
                    recipient, message = get_stuff(new_message.text)
                except:
                    pass
                else:
                    user.message(recipient, message)
    return handle

def post_stats(user, _):
    with txn() as session:
        user_mc_pairs = session.query(
            model.User, sqlalchemy.func.COUNT(model.Message.id)
        ).join(
            model.Message,
            model.Message.sender_id == model.User.id
        ).group_by(model.Message.sender_id).order_by(
            sqlalchemy.func.COUNT(model.Message.id).desc()
        ).limit(30).all()
    stats_string = 'Top Posters:\n{0}'.format(
        '\n'.join('{0}: {1}'.format(user.handle, message_count)
                  for user, message_count in user_mc_pairs)
    )
    user.profile.essays.message_me_if = stats_string


def get_handle_string(user, message):
    if user.username.lower() == message.sender.handle.lower():
        to_string = 'To: '
        user = message.recipient.handle
    else:
        to_string = ''
        user = message.sender.handle
    return '{0}<a href="http://www.okcupid.com/profile/{1}">{1}</a>'.format(to_string, user)


WALL_SIZE = 35000
def handle(user, messages):
    if len(messages) == 0:
        return
    messages = messages[::-1]

    message_groups = []
    current = []
    projected_length = 0

    my_timezone=timezone('US/Pacific')
    for message in messages:
        timestamp = my_timezone.localize(message.created_at)
        new_message = u'{0} {1}: {2}'.format(
            timestamp.strftime('%I:%M'), get_handle_string(user, message), message.text
        )
        message_length = len(new_message) + 2
        projected_length += message_length
        if projected_length > WALL_SIZE:
            message_groups.append(current)
            projected_length = message_length
            current = [new_message]
        else:
            current.append(new_message)
    currents = {essay_name: getattr(user.profile.essays, essay_name)
                for essay_name in user.profile.essays.essay_names}
    for message_group, essay_name in zip(message_groups, user.profile.essays.essay_names[1:-1]):
        wall_text = '\n\n'.join(message_group)
        if wall_text != currents[essay_name]:
            setattr(user.profile.essays, essay_name, '\n\n'.join(message_group))

def reset(user, ignore):
    with txn() as session:
        messages = model.Message.query_no_txn(session)
        handle(user, sorted(messages, key=lambda m: m.created_at))

def do_it():
    import okcupyd
    MessageHandler(okcupyd.User.from_credentials('pumpkinmania8', 'thisisforokc'),
                   reset, post_stats,
                   let_other_users_respond('aspensilver', 'shrewddrew')).handle_messages(sleep_time=20)
