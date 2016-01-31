# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime, timedelta
from json import loads
from lxml import html
from re import search
import logging

import simplejson

from .xpath import xpb
from . import util


CHAR_REPLACE = {
    u"′": "'",
    u'″': '"',
    u'“': '"',
    u'”': '"',
    u"’": "'",
    u"—": "-",
    u"–": "-",
    u"…": "...",
    u"🌲": " ",
    u'\u2019': "'",
}


log = logging.getLogger(__name__)


MessageInfo = namedtuple('MessageInfo', ('thread_id', 'message_id'))


class Messager(object):
    """Send Messages to an okcupid user."""

    def __init__(self, session):
        self._session = session

    def _get_authcode(self, username):
        response = self._session.okc_get('profile/{0}'.format(username))
        return get_authcode(html.fromstring(response.content))

    def message_request_parameters(self, username, message,
                                   thread_id, authcode):
        return {
            'ajax': 1,
            'sendmsg': 1,
            'r1': username,
            'body': message,
            'threadid': thread_id,
            'authcode': authcode,
            'reply': 1 if thread_id else 0,
            'from_profile': 1
        }

    def send(self, username, message, authcode=None, thread_id=None):
        authcode = authcode or self._get_authcode(username)
        params = self.message_request_parameters(
            username, message, thread_id or 0, authcode
        )
        response = self._session.okc_get('mailbox', params=params)
        response_dict = response.json()
        log.info(simplejson.dumps({'message_send_response': response_dict}))
        return MessageInfo(response_dict.get('threadid'), response_dict['msgid'])


@util.curry
def get_js_variable(html_response, variable_name):
    script_elements = xpb.script.apply_(html_response)
    html_response = u'\n'.join(script_element.text_content()
                               for script_element in script_elements)
    return search('var {0} = "(.*?)";'.format(variable_name), html_response).group(1)


get_authcode = get_js_variable(variable_name='AUTHCODE')
get_username = get_js_variable(variable_name='SCREENNAME')
get_id = get_js_variable(variable_name='CURRENTUSERID')
get_current_user_id = get_id
get_my_username = get_username


weekday_to_ordinal = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6
}


def parse_fancydate(fancydate_text):
    _, timestamp = fancydate_text.split('_')
    timestamp = '{0}.{1}'.format(timestamp[:10], timestamp[10:])
    return datetime.fromtimestamp(float(timestamp))


def parse_date_updated(date_updated_text):
    recognized = False
    for function in (parse_slashed_date, parse_abbreviated_date,
                     parse_time, parse_day_of_the_week, parse_contextual_date):
        parsed_time = function(date_updated_text)
        if parsed_time is not None:
            recognized = True
            break
    else:
        parsed_time = datetime.today()
    log_function = log.info if recognized else log.error
    log_function(simplejson.dumps({
        "matcher_function_name": function.__name__,
        "incoming_date": date_updated_text,
        "outgoing_date": parsed_time.strftime("%Y.%m.%d %H:%M"),
        "recognized": recognized
    }))
    return parsed_time


def parse_contextual_date(date_updated_text):
    if 'yesterday' in date_updated_text.lower():
        return datetime.now() - timedelta(days=1)
    if 'now' in date_updated_text.lower():
        return datetime.now()


def parse_slashed_date(date_updated_text):
    try:
        return datetime.strptime(date_updated_text, '%m/%d/%y')
    except:
        pass

def parse_abbreviated_date(date_updated_text):
    date_text = date_updated_text.replace(',', '')
    try:
        # Parse year if present in date_text; otherwise, use current year
        if date_text[-4].isdigit():
            return datetime.strptime(date_text, '%b %d %Y')
        else:
            parsed_time = datetime.strptime(date_text, '%b %d')
            return parsed_time.replace(year=datetime.now().year)
    except:
        pass

def parse_time(date_updated_text):
    try:
        time = datetime.strptime(date_updated_text, '%I:%M%p')
    except:
        pass
    else:
        today = datetime.today()
        parsed_time = time.replace(year=today.year, day=today.day,
                                   month=today.month)
        if parsed_time > datetime.now():
            parsed_time = parsed_time - timedelta(days=1)
        return parsed_time


def parse_day_of_the_week(date_updated_text):
    try:
        datetime.strptime(date_updated_text, '%A')
    except:
        pass
    else:
        return date_from_weekday(date_updated_text)


def date_from_weekday(weekday):
    today = datetime.now()
    incoming_weekday_ordinal = weekday_to_ordinal[weekday.lower()]
    today_ordinal = today.weekday()
    difference = (today_ordinal - incoming_weekday_ordinal
                  if today_ordinal > incoming_weekday_ordinal else
                  7 - incoming_weekday_ordinal + today_ordinal)
    return datetime.combine(today - timedelta(days=difference),
                            datetime.min.time())


def datetime_to_string(a_datetime):
    if a_datetime:
        return a_datetime.strftime('%H:%M:%S')


def get_locid(session, location):
    """
    Make a request to locquery resource to translate a string location
    search into an int locid.
    Returns
    ----------
    int
        An int that OKCupid maps to a particular geographical location.
    """
    locid = 0
    query_parameters = {
        'func': 'query',
        'query': location,
    }
    loc_query = session.get('http://www.okcupid.com/locquery',
                            params=query_parameters)
    p = html.fromstring(loc_query.content.decode('utf8'))
    js = loads(p.text)
    if 'results' in js and len(js['results']):
        locid = js['results'][0]['locid']
    return locid


def format_last_online(last_online):
    """
    Return the upper limit in seconds that a profile may have been
    online. If last_online is an int, return that int. Otherwise if
    last_online is a str, convert the string into an int.
    Returns
    ----------
    int
    """
    if isinstance(last_online, str):
        if last_online.lower() in ('day', 'today'):
            last_online_int = 86400  # 3600 * 24
        elif last_online.lower() == 'week':
            last_online_int = 604800  # 3600 * 24 * 7
        elif last_online.lower() == 'month':
            last_online_int = 2678400  # 3600 * 24 * 31
        elif last_online.lower() == 'year':
            last_online_int = 31536000  # 3600 * 365
        elif last_online.lower() == 'decade':
            last_online_int = 315360000  # 3600 * 365 * 10
        else: # Defaults any other strings to last hour
            last_online_int = 3600
    else:
        last_online_int = last_online
    return last_online_int


def update_looking_for(profile_tree, looking_for):
    """
    Update looking_for attribute of a Profile.
    """
    div = profile_tree.xpath("//div[@id = 'what_i_want']")[0]
    looking_for['gentation'] = div.xpath(".//li[@id = 'ajax_gentation']/text()")[0].strip()
    looking_for['ages'] = replace_chars(div.xpath(".//li[@id = 'ajax_ages']/text()")[0].strip())
    looking_for['near'] = div.xpath(".//li[@id = 'ajax_near']/text()")[0].strip()
    looking_for['single'] = div.xpath(".//li[@id = 'ajax_single']/text()")[0].strip()
    try:
        looking_for['seeking'] = div.xpath(".//li[@id = 'ajax_lookingfor']/text()")[0].strip()
    except:
        pass


def update_details(profile_tree, details):
    """
    Update details attribute of a Profile.
    """
    div = profile_tree.xpath("//div[@id = 'profile_details']")[0]
    for dl in div.iter('dl'):
        title = dl.find('dt').text
        item = dl.find('dd')
        if title == 'Last Online' and item.find('span') is not None:
            details[title.lower()] = item.find('span').text.strip()
        elif title.lower() in details and len(item.text):
            details[title.lower()] = item.text.strip()
        else:
            continue
        details[title.lower()] = replace_chars(details[title.lower()])


gender_to_orientation_to_gentation = {
    'm': {
        'straight': 'girls who like guys',
        'gay': 'guys who like guys',
        'bisexual': 'both who like bi guys'
    },
    'w': {
        'straight': 'guys who like girls',
        'gay': 'girls who like girls',
        'bisexual': 'both who like bi girls'
    },
    'f': {
        'straight': 'guys who like girls',
        'gay': 'girls who like girls',
        'bisexual': 'both who like bi girls'
    }
}


def get_default_gentation(gender, orientation):
    """Return the default gentation for the given gender and orientation."""
    gender = gender.lower()[0]
    orientation = orientation.lower()
    return gender_to_orientation_to_gentation[gender][orientation]


def replace_chars(astring):
    """
    Replace certain unicode characters to avoid errors when trying
    to read various strings.
    Returns
    ----------
    str
    """
    for k, v in CHAR_REPLACE.items():
        astring = astring.replace(k, v)
    return astring


def add_newlines(tree):
    """
    Add a newline character to the end of each <br> element.
    """
    for br in tree.xpath("*//br"):
        br.tail = u"\n" + br.tail if br.tail else u"\n"
