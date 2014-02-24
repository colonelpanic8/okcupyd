from json import loads
from re import search
from lxml import html
from pyokc.errors import AuthenticationError

CHAR_REPLACE = {
    "′": "'",
    '″': '"',
    '“': '"',
    '”': '"',
    "’": "'",
    "—": "-",
    "–": "-",
    "…": "...",
    }

def login(session, credentials):
    login_response = session.post('https://www.okcupid.com/login', data=credentials)
    root = html.fromstring(login_response.content.decode('utf8'))
    logged_in = False
    for script in root.iter('script'):
        if script.text and credentials['username'].lower() in script.text.lower():
            logged_in = True
            break
    if not logged_in:
        raise AuthenticationError('Could not log in with the credentials provided')
        
def get_additional_info(session):
    profile_response = session.get('https://www.okcupid.com/profile')
    profile_root = html.fromstring(profile_response.content.decode('utf8'))
    age = int(profile_root.xpath("//span[@id = 'ajax_age']/text()")[0])
    orientation = profile_root.xpath("//span[@id = 'ajax_orientation']/text()")[0]
    status = profile_root.xpath("//span[@id = 'ajax_status']/text()")[0]
    gender_result = profile_root.xpath("//span[@id = 'ajax_gender']/text()")[0]
    if gender_result == "M":
        gender = 'Male'
    elif gender_result == "F":
        gender = 'Female'
    return age, orientation, status, gender

def get_authcode(inbox_tree):
    authcode = ''
    for iframe in inbox_tree.xpath("//iframe[@id = 'ad_frame_sky_r']"):
        if 'src' in iframe.attrib: 
            source = iframe.attrib['src']
            re_search = search('authid=([a-z%0-9]+)', source)
            if re_search is not None:
                authcode = re_search.group(1)
    return authcode

def get_message_string(li_element, sender):
    if 'to_me' in li_element.attrib['class']:
        message_string = '{0}:'.format(sender)
    elif 'from_me' in li_element.attrib['class']:
        message_string = '{0}:'.format(li_element.find('a').attrib['title'])
    div = li_element.xpath(".//div[@class = 'message_body']")[0]
    message_string += div.text_content().replace(' \n \n', '\n').strip()
    return message_string
    
def get_locid(session, location):
    # if location.lower() == 'anywhere':
        # return 0
    query_parameters = {
        'func': 'query',
        'query': location,
        }
    loc_query = session.post('http://www.okcupid.com/locquery', data=query_parameters)
    p = html.fromstring(loc_query.content.decode('utf8'))
    js = loads(p.text)
    return js['locid']
    
def get_profile_basics(div, profiles):
    profile_info = {}
    if ('id' in div.attrib and len(div.attrib['id']) >= 4 and 
    'class' in div.attrib and div.attrib['class'] == 'match_card opensans'):
        name = div.attrib['id'][4:]
        if name.lower() not in [p.name.lower() for p in profiles]:
            age = None
            location = ''
            match = None
            for span in div.iterdescendants('span'):
                if 'class' in span.attrib and span.attrib['class'] == 'age':
                    age = int(span.text)
                if 'class' in span.attrib and span.attrib['class'] == 'location':
                    location = replace_chars(span.text)
            for desc_div in div.xpath(".//div[@class = 'percentages hide_on_hover ']"):
                if desc_div.text.replace(' ', '')[1] == '%':
                    match = int(desc_div.text.replace(' ', '')[0])
                else:
                    match = int(desc_div.text.replace(' ', '')[:2])
            if age is not None and location and match is not None:
                profile_info = {
                    'name': name,
                    'age': age,
                    'location': location,
                    'match': match,
                    }
    return profile_info
    
def format_last_online(last_online):
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
    status_parameter = 2  # single, default
    if status.lower() in ('not single', 'married'):
        status_parameter = 12
    if status.lower() == ('any'):
        status_parameter = 0
    return status_parameter
    
def get_percentages(profile_tree):
    percentage_list = []
    match_str = profile_tree.xpath("//span[@class = 'match']")[0].text
    friend_str = profile_tree.xpath("//span[@class = 'friend']")[0].text
    enemy_str = profile_tree.xpath("//span[@class = 'enemy']")[0].text
    for str in (match_str, friend_str, enemy_str):  
        if str[1] == '%':
            percentage_list.append(int(str[0]))
        else:
            percentage_list.append(int(str[:2]))
    return percentage_list
    
def update_essays(tree, essays):
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
    div = profile_tree.xpath("//div[@id = 'what_i_want']")[0]
    for li in div.iter('li'):
        if 'id' in li.attrib:
            if li.attrib['id'] == 'ajax_gentation':
                looking_for['gentation'] = li.text.strip()
            elif li.attrib['id'] == 'ajax_ages':
                looking_for['ages'] = li.text.strip()
                looking_for['ages'] = replace_chars(looking_for['ages'])
            elif li.attrib['id'] == 'ajax_near':
                looking_for['near'] = li.text.strip()
            elif li.attrib['id'] == 'ajax_single':
                looking_for['single'] = li.text.strip()
            elif li.attrib['id'] == 'ajax_lookingfor':
                looking_for['seeking'] = li.text.strip()               
                    
def update_details(profile_tree, details):
    div = profile_tree.xpath("//div[@id = 'profile_details']")[0]
    for dl in div.iter('dl'):
        title = dl.find('dt').text
        if title == 'Last Online' and dl.find('dd').find('span') is not None:
            details[title.lower()] = dl.find('dd').find('span').text.strip()            
        elif title.lower() in details:    
            details[title.lower()] = dl.find('dd').text.strip()
        details[title.lower()] = replace_chars(details[title.lower()])
        
def get_looking_for(gender, orientation):
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
    
def get_profile_gentation(tree):
    age = tree.xpath("//span[@id = 'ajax_age']")[0].text
    gender_result = tree.xpath("//span[@id = 'ajax_gender']")[0].text
    orientation = tree.xpath("//span[@id = 'ajax_orientation']")[0].text
    status = tree.xpath("//span[@id = 'ajax_status']")[0].text
    if gender_result == "M":
        gender = 'Male'
    elif gender_result == "F":
        gender = 'Female'
    return age, gender, orientation, status

def replace_chars(astring):
    for k, v in CHAR_REPLACE.items():
        astring = astring.replace(k, v)
    return astring
                
def add_newlines(tree):
    for br in tree.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
            