from json import loads
from re import search
from lxml import html

from .errors import AuthenticationError, ProfileNotFoundError


CHAR_REPLACE = {
    "′": "'",
    '″': '"',
    '“': '"',
    '”': '"',
    "’": "'",
    "—": "-",
    "–": "-",
    "…": "...",
    "🌲": " ",
    }

def login(session, credentials, headers):
    """
    Make a POST request to OKCupid using the login credentials provided
    by the user.
    """
    login_response = session.post('https://www.okcupid.com/login', data=credentials, headers=headers)
    if login_response.url == 'https://www.okcupid.com/login':
        raise AuthenticationError('Could not log in with the credentials provided')

def get_additional_info(tree):
    """
    Make a request to OKCupid to get a user's age, gender, orientation,
    and relationship status.
    """
    age = int(tree.xpath("//*[@id = 'ajax_age']/text()")[0].strip())
    orientation = tree.xpath("//*[@id = 'ajax_orientation']/text()")[0].strip()
    status = tree.xpath("//*[@id = 'ajax_status']/text()")[0].strip()
    gender_result = tree.xpath("//*[@id = 'ajax_gender']/text()")[0].strip()
    if gender_result == "M":
        gender = 'Male'
    elif gender_result == "F":
        gender = 'Female'
    return age, gender, orientation, status

def get_authcode(inbox_tree):
    """
    Get the current authcode necessary to send a message to another
    profile.
    """
    authcode = ''
    for source in inbox_tree.xpath("//iframe[@id = 'ad_frame_sky_r']/@src"):
        re_search = search('authid=([a-z%0-9]+)', source)
        if re_search is not None:
            authcode = re_search.group(1)
    return authcode

def get_message_string(li_element, sender):
    """
    Parse <li> element to get a string containing a message from
    one profile to another.
    Returns
    ---------
    str
    """
    if 'to_me' in li_element.attrib['class']:
        message_string = '{0}: '.format(sender)
    elif 'from_me' in li_element.attrib['class']:
        message_string = 'Me: '
    div = li_element.xpath(".//div[@class = 'message_body']")[0]
    message_string += div.text_content().replace(' \n \n', '\n').strip()
    return message_string

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
    loc_query = session.post('http://www.okcupid.com/locquery', data=query_parameters)
    p = html.fromstring(loc_query.content.decode('utf8'))
    js = loads(p.text)
    if 'results' in js and len(js['results']):
        locid = js['results'][0]['locid']
    return locid

def get_rating(div):
    """
    Get the rating from a match card.
    Parameters
    ---------
    div : element
        Element used by xpath.
    Returns
    ---------
    int
        The rating you've given this user.
    """
    try:
        rating_div = div.xpath(".//li[@class = 'current-rating']")
        rating_style = rating_div[0].attrib['style']
        width_percent = int(''.join(c for c in rating_style if c.isdigit()))
        return int((width_percent / 100) * 5)
    except IndexError:
        return 0

def get_contacted(div):
    """
    Get whether you've contacted this user.
    Parameters
    ---------
    div : element
        Element used by xpath.
    Returns
    ---------
    bool
        Whether you've contacted this user or not.
    """
    return bool(div.xpath(".//span[@class = 'fancydate']"))


class MatchCardExtractor(object):

    def __init__(self, div):
        self._div = div

    @property
    def username(self):
        return self._div.xpath(".//div[@class = 'username']")[0].text_content()

    @property
    def age(self):
        return int(self._div.xpath(".//span[@class = 'age']/text()")[0])

    @property
    def location(self):
        return replace_chars(self._div.xpath(".//span[@class = 'location']/text()")[0])

    @property
    def id(self):
        try:
            raw_id = self._div.xpath(".//li[@class = 'current-rating']/@id")[0]
            return search(r'\d{2,}', raw_id).group()
        except IndexError:
            return self._div.xpath(".//button[@id = 'personality-rating']/@data-tuid")[0]

    @property
    def match_percentage(self):
        return int(self._div.xpath(".//div[@class = 'percentage_wrapper match']")[0].xpath(".//span[@class = 'percentage']")[0].text.strip('%'))

    @property
    def enemy_percentage(self):
        return int(self._div.xpath(".//div[@class = 'percentage_wrapper enemy']")[0].xpath(".//span[@class = 'percentage']")[0].text.strip('%'))

    @property
    def rating(self):
        try:
            rating_div = self._div.xpath(".//li[@class = 'current-rating']")
            rating_style = rating_div[0].attrib['style']
            width_percent = int(''.join(c for c in rating_style if c.isdigit()))
            return int((width_percent / 100) * 5)
        except IndexError:
            return 0

    @property
    def contacted(self):
        return bool(self._div.xpath(".//span[@class = 'fancydate']"))

    @property
    def as_dict(self):
        return {
            'name': self.username,
            'age': self.age,
            'location': self.location,
            'match': self.match_percentage,
            'enemy': self.enemy_percentage,
            'id': self.id,
            'rating': self.rating,
            'contacted': self.contacted
        }


def get_profile_basics(div, profiles):
    return MatchCardExtractor(div).as_dict


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

def format_status(status):
    """
    Returns the int that OKCupid maps to relationship status for
    searching profiles.
    Returns
    ----------
    int
    """

    status_parameter = 2  # single, default
    if status.lower() in ('not single', 'married'):
        status_parameter = 12
    elif status.lower() == 'any':
        status_parameter = 0
    return status_parameter

def get_percentages(profile_tree):
    """
    Parse element tree to return a profile's match, friend, and enemy
    percentages with the user.
    Returns
    ----------
    list of int
    """
    percentage_list = []
    try:
        match_str = enemy_str = ""
        for box in profile_tree.xpath("//div[@class = 'percentbox']"):
            if box.xpath(".//span[@class = 'percentlabel']/text()")[0].lower() == 'match':
                match_str = box.xpath(".//span[@class = 'percent']/text()")[0]
            else:
                enemy_str = box.xpath(".//span[@class = 'percent']/text()")[0]
        for str in (match_str, enemy_str):
            if str and str[1] == '%':
                percentage_list.append(int(str[0]))
            elif str:
                percentage_list.append(int(str[:2]))
            else:
                percentage_list.append("")
        return percentage_list
    except IndexError:
        raise ProfileNotFoundError('Could not find the profile specified')

def get_profile_id(tree):
    """
    Return a unique profile id string.
    """
    try:
        js_call_string = tree.xpath("//a[@class = 'one-star']/@href")[0]
        return search(r'\d{2,}', js_call_string).group()
    except IndexError:
        return tree.xpath("//button[@id = 'rate_user_profile']/@data-tuid")[0]
        # <button id="rate_user_profile" data-tuid="2538582662150475561"

def update_essays(tree, essays):
    """
    Update essays attribute of a Profile.
    """
    add_newlines(tree)
    for div in tree.xpath("//div[@class = 'essay content saved locked other ']"):
        title = div.find('a').text.replace("’", "'")
        desc_div = div.xpath(".//div[contains(@id, 'essay_text_')]")[0]
        text = desc_div.text_content().replace('\n\n', '\n').strip()
        for k, v in CHAR_REPLACE.items():
            text = text.replace(k, v)
        if title == "My self-summary":
            essays['self summary'] = text
        elif title == "What I'm doing with my life":
            essays['life'] = text
        elif title == "I'm really good at":
            essays['good at'] = text
        elif title == "The first things people usually notice about me":
            essays['first things'] = text
        elif title == "Favorite books, movies, shows, music, and food":
            essays['favorites'] = text
        elif title == "The six things I could never do without":
            essays['six things'] = text
        elif title == "I spend a lot of time thinking about":
            essays['thinking'] = text
        elif title == "On a typical Friday night I am":
            essays['friday night'] = text
        elif title == "The most private thing I'm willing to admit":
            essays['private thing'] = text
        elif title == "You should message me if":
            essays['message me if'] = text

def update_looking_for(profile_tree, looking_for):
    """
    Update looking_for attribute of a Profile.
    """
    div = profile_tree.xpath("//div[@id = 'what_i_want']")[0]
    looking_for['gentation'] = div.xpath(".//li[@id = 'ajax_gentation']/text()")[0].strip()
    looking_for['ages'] = replace_chars(div.xpath(".//li[@id = 'ajax_ages']/text()")[0].strip())
    looking_for['near'] = div.xpath(".//li[@id = 'ajax_near']/text()")[0].strip()
    looking_for['single'] = div.xpath(".//li[@id = 'ajax_single']/text()")[0].strip()
    looking_for['seeking'] = div.xpath(".//li[@id = 'ajax_lookingfor']/text()")[0].strip()

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
    if gender == 'Male':
        if orientation == 'Straight':
            looking_for = 'girls who like guys'
        elif orientation == 'Gay':
            looking_for = 'guys who like guys'
        elif orientation == 'Bisexual':
            looking_for = 'both who like bi guys'
    elif gender == 'Female':
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
