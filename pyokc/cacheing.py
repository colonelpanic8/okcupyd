import datetime

import simplejson

from . import messaging
from .statistics import Statistics
from .user import User


# TODO: This code is pretty crappy and should be cleaned up.
def save_message_threads(filename, message_threads):
    with open(filename, 'w') as file_object:
        for thread in message_threads:
            file_object.write(simplejson.dumps(thread.as_dict) + '\n')


def load_message_threads(filename):
    with open(filename, 'r') as file_object:
        for line in file_object.readlines():
            thread_dictionary = simplejson.loads(line)
            thread_dictionary['date'] = datetime.datetime.strptime(thread_dictionary['date'], '%Y-%m-%d').date()
            thread_dictionary['messages'] = [messaging.Message(**message_dict) for message_dict in thread_dictionary['messages']]
            yield messaging.MessageThread.restore(**thread_dictionary)


def get_statistics_with_cached_data(user=None,
                                    attractiveness_file='attractiveness_cache.json',
                                    message_threads_file='message_threads.json'):
    user = user or User()
    mts = list(load_message_threads(message_threads_file))
    statistics = Statistics(user, mts)
    with open(attractiveness_file) as file_object:
        statistics._attractiveness_finder._cache = simplejson.loads(file_object.read())
    return statistics


def save_data_on_statistics_object(statistics,
                                   attractiveness_file='attractiveness_cache.json',
                                   message_threads_file='message_threads.json'):
    save_message_threads(message_threads_file, statistics.threads)
    with open(attractiveness_file, 'w') as file_object:
        file_object.write(simplejson.dumps(statistics._attractiveness_finder._cache))
