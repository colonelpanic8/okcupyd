import datetime
import time
import random
import logging

import simplejson


log = logging.getLogger(__name__)
log.addHandler(logging.FileHandler('sent_messages.json'))

hour = 60*60

real_messages = ("""Let's make this fun -- somewhere nearby and not too stodgy :)

I'm excited to make this a date, so send me a message back.""",
                 """Let's make this fun -- somewhere nearby and not too stodgy :)

I'm excited to make this a date, so send me a message and make it happen.""",
                 'Would you like to go on a bike ride to Ocean Beach?',
                 'Would you like to grab a drink this week?')


class ContinuousMessageSender(object):

    def __init__(self, search_manager, messages=real_messages, message_interval=120):
        self._messages = messages
        self._search_manager = search_manager
        self._already_messaged = set()
        self._message_interval = message_interval

    def random_message(self, messages):
        return messages[random.randint(0, len(messages)-1)]

    def send_messages(self, send_interval=hour/2, sleep_interval=hour/2, message_interval=None):
        while True:
            self.send_messages_for_interval(send_interval, message_interval=message_interval)
            self.sleep_for_interval(sleep_interval)

    def send_messages_for_interval(self, send_interval, message_interval=None):
        message_interval = message_interval or self._message_interval
        start_of_interval = time.time()
        while time.time() - start_of_interval < send_interval:
            profiles = self._search_manager.get_profiles()
            for profile in profiles:
                message = self.random_message(self._messages)
                log.info(simplejson.dumps({'message': message, 'username': profile.username,
                                           'time': time.time()}))
                if profile.username in self._already_messaged:
                    log.info(simplejson.dumps({'skipped': profile.username}))
                    continue
                profile.message(message)
                self._already_messaged.add(profile.username)
                time.sleep(message_interval)

    def sleep_for_interval(self, interval, log_interval=15):
        start = time.time()
        stop = start + interval
        while time.time() < stop:
            log.info(simplejson.dumps({'sleep_start': start, 'sleep_end': stop,
                                       'now': datetime.datetime.now().strftime('%H:%M:%S')}))
            time.sleep(log_interval)
