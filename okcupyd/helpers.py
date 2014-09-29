# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime, date
from json import loads
from lxml import html, etree
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

    def __init__(self, session):
        self._session = session

    def _get_authcode(self, username):
        response = self._session.get(
            'https://www.okcupid.com/profile/{0}'.format(username)
        ).content.decode('utf8')
        return get_authcode(response)

    def message_request_parameters(self, username, message, thread_id, authcode):
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
        params = self.message_request_parameters(username, message,
                                                 thread_id or 0, authcode)
        response = self._session.get('https://www.okcupid.com/mailbox', params=params)
        response_dict = response.json()
        log.info(simplejson.dumps({'message_send_response': response_dict}))
        return MessageInfo(response_dict['threadid'], response_dict['msgid'])


def get_additional_info(tree):
    age = int(xpb.span(id='ajax_age').get_text_(tree).strip())
    orientation = tree.xpath("//*[@id = 'ajax_orientation']/text()")[0].strip()
    status = tree.xpath("//*[@id = 'ajax_status']/text()")[0].strip()
    gender_result = tree.xpath("//*[@id = 'ajax_gender']/text()")[0].strip()
    location = tree.xpath("//*[@id = 'ajax_location']/text()")[0].strip()
    if gender_result == "M":
        gender = 'Male'
    elif gender_result == "F":
        gender = 'Female'
    return age, gender, orientation, status, location


utf8_parser = etree.XMLParser(encoding='utf-8')


@util.n_partialable
def get_js_variable(html_response, variable_name):
    script_elements = xpb.script.apply_(html_response)
    html_response = '\n'.join(script_element.text_content()
                              for script_element in script_elements)
    return search('var {0} = "(.*?)";'.format(variable_name), html_response).group(1)


get_authcode = get_js_variable(variable_name='AUTHCODE')
get_username = get_js_variable(variable_name='SCREENNAME')
get_id = get_js_variable(variable_name='CURRENTUSERID')
get_current_user_id = get_id
get_my_username = get_username


def parse_date_updated(date_updated_text):
    if '/' in date_updated_text:
        return datetime.strptime(date_updated_text, '%m/%d/%y').date()

    if date_updated_text[-2] == ' ':
        month, day = date_updated_text.split()
        date_updated_text = '{0} 0{1}'.format(month, day)

    try:
        return datetime.strptime(date_updated_text, '%b %d').replace(year=datetime.now().year).date()
    except:
        return date.today()


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
    loc_query = session.get('http://www.okcupid.com/locquery', params=query_parameters)
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


def get_looking_for(gender, orientation):
    """
    Return a string containing the default gender/orientation of a
    search if no value has been provided to the looking_for kwarg.
    Returns
    ----------
    str
    """
    looking_for = ''
    if gender.lower() in ('male', 'm',):
        if orientation == 'Straight':
            looking_for = 'girls who like guys'
        elif orientation == 'Gay':
            looking_for = 'guys who like guys'
        elif orientation == 'Bisexual':
            looking_for = 'both who like bi guys'
    elif gender.loiwer() in ('female', 'f'):
        if orientation == 'Straight':
            looking_for = 'guys who like girls'
        elif orientation == 'Gay':
            looking_for = 'girls who like girls'
        elif orientation == 'Bisexual':
            looking_for = 'both who like bi girls'
    return looking_for


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
        br.tail = "\n" + br.tail if br.tail else "\n"
