import logging
import time

import simplejson

import pyokc


log = logging.getLogger(__name__)


class HotOrNotBot(object):

    def __init__(self, user, attractiveness_finder=None, message_logger=None):
        self._user = user
        self._attractiveness_finder = attractiveness_finder or pyokc.AttractivenessFinder()
        self._message_logger = message_logger

    def continuously_respond_to_messages(self):
        while True:
            self.respond_to_messages()
            time.sleep(30)

    def respond_to_messages(self):
        for user, requested_usernames in self.get_requests():
            if self._message_logger:
                self._message_logger.log_request(user, requested_usernames)
            log.debug("Sending attractiveness of {0} to {1}".format(
                requested_usernames, user))
            message = self._build_message(requested_usernames)
            log.debug(message)
            self._user.message(user, message)

    def get_requests(self):
        for thread in self._user.inbox.refresh(use_existing=False):
            log.debug("Reading thread from {0}".format(thread.correspondent))
            messages = thread.messages[::-1]
            requested_usernames = []
            for message in messages:
                if message.sender == self._user.username:
                    break
                else:
                    words = message.content.split()
                    if len(words) == 1:
                        requested_usernames.append(words[0])
            if requested_usernames:
                yield thread.correspondent, requested_usernames
            self._message_logger.log_thread(thread)
            thread.delete()

    def _build_message(self, requested_usernames):
        return '\n'.join('{0}: {1}'.format(username,
                                           self._build_message_line(username))
                         for username in requested_usernames)

    def _build_message_line(self, username):
        attractiveness = self._attractiveness_finder.find_attractiveness(username)
        if attractiveness is None:
            return 'Not Enough Data'
        else:
            return '{0} out of 5'.format((attractiveness//2000) + 1)




def out_of_five(attractiveness):
    return '{0} out of 5'.format((attractiveness//2000) + 1)


class Introducer(object):

    def __init__(self):
        self.user = pyokc.User()
        self.met = set()
        self.find_attractiveness = pyokc.AttractivenessFinder().find_attractiveness

    def run(self):
        while True:
            self.do_introductions()
            time.sleep(5)
            for thread in self.user.outbox.refresh():
                thread.delete()

    def do_introductions(self):
        profiles = pyokc.search(self.user._session, order_by='SPECIAL_BLEND')
        print(profiles)
        for profile in profiles:
            self.introduce(profile)

    def introduce(self, profile):
        if profile.username in self.met:
            return
        attractiveness = self.find_attractiveness(profile.username)
        if attractiveness is not None and profile.username not in self.met:
            print(profile.username)
            self.user.message(profile, self.build_introductory_message(profile,
                                                                       attractiveness))
        self.met.add(profile.username)

    def build_introductory_message(self, profile, attractiveness):
        return """Hi {0},
The OKCupid community rates your profile at {1} stars on average.

Send me a message containing only the username of another user and I will reply with their attractiveness.""".format(profile.username, out_of_five(attractiveness))


class MessageLogger(object):

    def __init__(self, threads_filename, requests_filename):
        self.threads_filename = threads_filename
        self.requests_filename = requests_filename

    def log_thread(self, message_thread):
        with open(self.threads_filename, 'a') as threads_file:
            threads_file.write(simplejson.dumps(message_thread.as_dict) + '\n')

    def log_request(self, username, requested_usernames):
        with open(self.requests_filename, 'a') as requests_file:
            requests_file.write(simplejson.dumps({
                'username': username,
                'requested_usernames': requested_usernames
            }) + '\n')


if __name__ == '__main__':
    import logging; logging.basicConfig(level=logging.DEBUG)
    message_logger = MessageLogger('logs/threads.json', 'logs/requests.json')
    HotOrNotBot(pyokc.User(), message_logger=message_logger).continuously_respond_to_messages()
