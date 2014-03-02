import re
from lxml import html
from pyokc import helpers
from pyokc import magicnumbers
from pyokc.objects import MessageThread, UserQuestion, ProfileQuestion, Session
  
class User:
    """
    Represent an OKCupid user.
    Parameters
    ----------
    username : str
        The username for your OKCupid account.
    password : str
        The password for your OKCupid account.
    Raises
    ----------
    AuthenticationError
        If you are unable to login with the username and password
        provided.
    """
    def __init__(self, username, password):
        self.username = username
        self.inbox = []
        self.outbox = []
        self.drafts = []
        self.questions = []
        self.visitors = []
        self._session = Session()
        credentials = {'username': username, 'password': password, 'dest': '/home'}
        helpers.login(self._session, credentials)
        profile_response = self._session.get('https://www.okcupid.com/profile')
        profile_tree = html.fromstring(profile_response.content.decode('utf8'))
        self.age, self.gender, self.orientation, self.status = helpers.get_additional_info(profile_tree)
        self.update_mailbox(pages=1)
        self.update_visitors()
        
    def update_mailbox(self, box='inbox', pages=10):
        """
        Update either `self.inbox`, `self.outbox`, or `self.drafts` with
        MessageThread objects that represent a conversation with another
        user.
        Parameters
        ----------
        box : str, optional
            Specifies which box to update. Valid choices are inbox, outbox,
            drafts and all. Update the inbox by default.
        """
        for i in ('inbox', 'outbox', 'drafts'):
            if box.lower() != 'all':
                i = box.lower()
            if i.lower() == 'inbox':
                folder_number = 1
                update_box = self.inbox
                direction = 'from'
            elif i.lower() == 'outbox':
                folder_number = 2
                update_box = self.outbox
                direction = 'to'
            elif i.lower() == 'drafts':
                # What happened to folder 3? Who knows.
                folder_number = 4 
                update_box = self.drafts
                direction = 'to'
            for page in range(pages):
                inbox_data = {
                    'low': 30*page + 1, 
                    'folder': folder_number,
                    }
                get_messages = self._session.post('http://www.okcupid.com/messages', data=inbox_data)
                inbox_tree = html.fromstring(get_messages.content.decode('utf8'))
                messages_container = inbox_tree.xpath("//ul[@id = 'messages']")[0]
                for li in messages_container.iterchildren('li'):
                    threadid = li.attrib['data-threadid'] + str(page)
                    if threadid not in [thread.threadid for thread in update_box]:
                        sender = li.xpath(".//span[@class = 'subject']")[0].text_content()
                        if len(sender) > 3 and sender[:3] == 'To ':
                            sender = sender[3:]
                        if 'unreadMessage' in li.attrib['class']:
                            unread = True
                        else:
                            unread = False
                        update_box.append(MessageThread(sender, threadid, unread, self._session, direction))
                next_disabled = inbox_tree.xpath("//li[@class = 'next disabled']")
                if len(next_disabled):
                    break
            if box.lower() != 'all':
                break
        
    def message(self, username, message_text):
        """
        Send a message to the username specified.
        Parameters
        ----------
        username : str or Profile
            Username of the profile that is being messaged.
        message_text : str
            Text body of the message.
        """
        threadid = ''
        if isinstance(username, Profile):
            username == username.name
        for thread in self.inbox[::-1]: # reverse, find most recent messages first
            if thread.sender.lower() == username.lower():
                threadid = thread.threadid
                break
        get_messages = self._session.get('http://www.okcupid.com/messages')
        inbox_tree = html.fromstring(get_messages.content.decode('utf8'))
        authcode = helpers.get_authcode(inbox_tree)
        msg_data = {
            'ajax': '1', 
            'sendmsg': '1',
            'r1': username,
            'body': message_text,
            'threadid': threadid,
            'authcode': authcode,
            'reply': '1',
            }
        send_msg = self._session.post('http://www.okcupid.com/mailbox', data=msg_data)

    def search(self, location='', radius=25, number=18, age_min=18, age_max=99,
        order_by='match', last_online='week', status='single',
        height_min=None, height_max=None, looking_for='', **kwargs):
        """
        Search OKCupid profiles, return a list of matching profiles.
        See the search page on OKCupid for a better idea of the
        arguments expected.
        Parameters
        ----------
        location : string, optional
            Location of profiles returned. Accept ZIP codes, city
            names, city & state combinations, and city & country
            combinations. Default to user location if unable to
            understand the string or if no value is given.
        radius : int, optional
            Radius in miles searched, centered on the location.
        number : int, optional
            Number of profiles returned. Default to 18, which is the
            same number that OKCupid returns by default.
        age_min : int, optional
            Minimum age of profiles returned. Cannot be lower than 18.
        age_max : int, optional
            Maximum age of profiles returned. Cannot by higher than 99.
        order_by : str, optional
            Order in which profiles are returned.
        last_online : str, optional
            How recently online the profiles returned are. Can also be
            an int that represents seconds.
        status : str, optional
            Dating status of profiles returned. Default to 'single'
            unless the argument is either 'not single', 'married', or
            'any'.
        height_min : int, optional
            Minimum height in inches of profiles returned.
        height_max : int, optional
            Maximum height in inches of profiles returned.
        looking_for : str, optional
            Describe the gender and orientation of profiles returned.
            If left blank, return some variation of "guys/girls who
            like guys/girls" or "both who like bi girls/guys, depending
            on the user's gender and orientation.
        smokes : list of str, optional
            Smoking habits of profiles returned.
        drinks : list of str, optional
            Drinking habits of profiles returned.
        drugs : list of str, optional
            Drug habits of profiles returned.
        education : list of str, optional
            Highest level of education attained by profiles returned.
        job : list of str, optional
            Industry in which the profile users work.
        income : list of str, optional
            Income range of profiles returned.
        religion : list of str, optional
            Religion of profiles returned.
        offspring : list of str, optional
            Whether the profiles returned have or want children.
        pets : list of str, optional
            Dog/cat ownership of profiles returned.
        diet : list of str, optional
            Dietary restrictions of profiles returned.
        sign : list of str, optional
            Astrological sign of profiles returned.       
        ethnicity : list of str, optional
            Ethnicity of profiles returned.
        join_date : int or str, optional
            Either a string describing the profile join dates ('last
            week', 'last year' etc.) or an int indicating the number
            of maximum seconds from the moment of joining OKCupid.
        keywords : str, optional
            Keywords that the profiles returned must contain. Note that
            spaces separate keywords, ie. `keywords="love cats"` will
            return profiles that contain both "love" and "cats" rather
            than the exact string "love cats".
        """
        if not len(looking_for):
            looking_for = helpers.get_looking_for(self.gender, self.orientation)
        looking_for_number = magicnumbers.seeking[looking_for.lower()]
        if age_min < 18:
            age_min = 18
        if age_max > 99:
            age_max = 99
        if age_min > age_max:
            age_min, age_max = age_max, age_min
        locid = helpers.get_locid(self._session, location)
        last_online_int = helpers.format_last_online(last_online)
        status_parameter = helpers.format_status(status)
        search_parameters = {
            'filter1': '0,{0}'.format(looking_for_number),
            'filter2': '2,{0},{1}'.format(age_min, age_max),
            'filter3': '5,{0}'.format(last_online_int),
            'filter4': '35,{0}'.format(status_parameter),
            'locid': locid, 
            'timekey': 1,
            'matchOrderBy': order_by.upper(),
            'custom_search': 0,
            'fromWhoOnline': 0,
            'mygender': self.gender[0],
            'update_prefs': 1,
            'sort_type': 0,
            'sa': 1,
            'using_saved_search': '',
            'count': number,
            }
        filter_no = '5'
        if location.lower() != 'anywhere':
            search_parameters['filter5'] = '3,{0}'.format(radius)
            filter_no = str(int(filter_no) + 1)
        if height_min is not None or height_max is not None:
            height_query = magicnumbers.get_height_query(height_min, height_max)
            search_parameters['filter{0}'.format(filter_no)] = height_query
            filter_no = str(int(filter_no) + 1)
        for key, value in kwargs.items():
            if key in ['smokes', 'drinks', 'drugs', 'education', 'job',
            'income', 'religion', 'diet', 'sign', 'ethnicity'] and len(value):
                search_parameters['filter{0}'.format(filter_no)] = magicnumbers.get_options_query(key, value)
                filter_no = str(int(filter_no) + 1)
            elif key == 'pets':
                dog_query, cat_query = magicnumbers.get_pet_queries(value)
                search_parameters['filter{0}'.format(filter_no)] = dog_query
                filter_no = str(int(filter_no) + 1)
                search_parameters['filter{0}'.format(filter_no)] = cat_query
                filter_no = str(int(filter_no) + 1)
            elif key == 'offspring':
                kids_query = magicnumbers.get_kids_query(value)
                search_parameters['filter{0}'.format(filter_no)] = kids_query
                filter_no = str(int(filter_no) + 1)
            elif key == 'languages':
                language_query = magicnumbers.language_map[value.title()]
                search_parameters['filter{0}'.format(filter_no)] = '22,{0}'.format(language_query)
                filter_no = str(int(filter_no) + 1)
            elif key == 'join_date':
                join_date_query = magicnumbers.get_join_date_query(value)
                search_parameters['filter{0}'.format(filter_no)] = join_date_query
                filter_no = str(int(filter_no) + 1)
            elif key == 'keywords':
                search_parameters['keywords'] = value
        profiles_request = self._session.post('http://www.okcupid.com/match', data=search_parameters)
        profiles_tree = html.fromstring(profiles_request.content.decode('utf8'))
        profiles = []
        for div in profiles_tree.iter('div'):
            info = helpers.get_profile_basics(div, profiles)
            if len(info):
                profiles.append(Profile(self._session, info['name'], info['age'],
                                     info['location'], info['match'], enemy=info['enemy'],
                                     id=info['id']))
        return profiles
        
    def visit(self, username, update_pics=False):
        """Visit another user's profile. Automatically update the
        `essays`, `details`, and `looking_for` attributes of the
        visited profile. Accept either a string or a Profile object as
        an argument. Note that unless your profile is set to browse
        anonymously on OKCupid, you are likely to show up on this
        user's visitors list.
        Parameters
        ---------
        username : str, Profile
            Username of the profile to visit. Can be either a string or a
            Profile object.
        update_pics : Bool
            Determines whether or not update_pics() is automatically
            called for this profile.
        Returns
        ---------
        Profile
            An instance of Profile containing the visited user's
            information.
        """
        if isinstance(username, Profile):
            prfl = username
        else: # string
            prfl = Profile(self._session, username)
        params = {
            'cf': 'leftbar_match',
            'leftbar_match': 1,
            }
        profile_request = self._session.post('http://www.okcupid.com/profile/{0}'.format(prfl.name), data=params)
        profile_tree = html.fromstring(profile_request.content.decode('utf8'))
        prfl.match, prfl.friend, prfl.enemy = helpers.get_percentages(profile_tree)
        prfl.age, prfl.gender, prfl.orientation, prfl.status = helpers.get_additional_info(profile_tree)
        helpers.update_essays(profile_tree, prfl.essays)
        helpers.update_looking_for(profile_tree, prfl.looking_for)
        helpers.update_details(profile_tree, prfl.details)
        # If update_pics is False, you will need to call Profile.update_pics()
        # manually if you wish to access urls in this profile's pics attribute,
        # however this method will be approximately 3 seconds quicker because
        # it makes only 1 request instead of 2.
        if update_pics:
            prfl.update_pics()
        if prfl._id is None:
            prfl._id = helpers.get_profile_id(profile_tree)
        return prfl
        
    def update_questions(self):
        """
        Update `self.questions` with a sequence of question objects,
        whose properties can be found in objects.py. Note that this
        can take a while due to OKCupid displaying only ten questions
        on each page, potentially requiring a large number of requests.
        """
        count = 0
        question_number = 0
        keep_going = True
        while keep_going:
            questions_data = {
                'low': 1 + 10*count,
                }
            get_questions = self._session.post('http://www.okcupid.com/profile/{0}/questions'.format(self.username), data=questions_data)
            tree = html.fromstring(get_questions.content.decode('utf8'))
            for div in tree.iter('div'):
                if 'id' in div.attrib and re.match(r'question_(\d+)', div.attrib['id']):
                    question_number += 1
                    explanation = ''
                    number = re.match(r'question_(\d+)', div.attrib['id']).group(1)
                    text = helpers.replace_chars(div.xpath(".//p[@class = 'qtext']")[0].text)
                    answer_eles = div.xpath(".//li")
                    answers = {}
                    # Use a dictionary/regex for the answer values
                    # because occasionally the numbers are not sequential
                    for ele in answer_eles:
                        value = re.match(r'self_answers_\d+_(\d+)', ele.attrib['id']).group(1)
                        answers[value] = ele.text
                    acceptable_answers = [ele.text for ele in answer_eles if ele.attrib['class'] in (' match', 'mine match')]
                    importance_no = div.xpath(".//input[@id = 'question_{0}_importance']/@value".format(number))[0]
                    if importance_no == '5':
                        importance = 'Irrelevant'
                    elif importance_no == '4':
                        importance = 'A little important'
                    elif importance_no == '3':
                        importance = 'Somewhat important'
                    elif importance_no == '2':
                        importance = 'Very important'
                    elif importance_no == '1':
                        importance = 'Mandatory'
                    explanation_p = div.xpath(".//p[@class = 'explanation']")
                    if explanation_p[0].text is not None:
                        explanation = explanation_p[0].text
                    answer_int = int(div.xpath(".//input[@id = 'question_{0}_answer']/@value".format(number))[0])
                    if question_number > 1 and text not in [q.text for q in self.questions]:
                        user_answer = answers[str(answer_int)]
                        self.questions.append(UserQuestion(text, answers, user_answer, explanation, self, acceptable_answers, importance))
            next = tree.xpath("//a[text() = 'Next']")
            if not len(next) or 'href' not in next[0].attrib:
                keep_going = False
            else:
                count += 1
                
    def read(self, thread):
        """
        Update messages attribute of a thread object with a list of
        messages to and from the main User and another profile.
        Parameters
        ----------
        thread : MessageThread
            Instance of MessageThread whose `messages` attribute you
            wish to update.
        """
        thread_data = {'readmsg': 'true', 'threadid': thread.threadid[:-1], 'folder': 1}
        get_thread = self._session.get('http://www.okcupid.com/messages', params=thread_data)
        thread_tree = html.fromstring(get_thread.content.decode('utf8'))
        helpers.add_newlines(thread_tree)
        for li in thread_tree.iter('li'):
            if 'class' in li.attrib and li.attrib['class'] in ('to_me', 'from_me', 'from_me preview'):
                message_string = helpers.get_message_string(li, thread.sender)
                thread.messages.append(message_string)
                
    def update_visitors(self):
        """
        Update self.visitors with a Profile instance for each
        visitor on your visitors list.
        """
        get_visitors = self._session.get('http://www.okcupid.com/visitors')
        tree = html.fromstring(get_visitors.content.decode('utf8'))
        divs = tree.xpath("//div[@class = 'user_row_item clearfix  ']")
        for div in divs:
            name = div.xpath(".//a[@class = 'name']/text()")[0]
            age = int(div.xpath(".//div[@class = 'userinfo']/span[@class = 'age']/text()")[0])
            location = div.xpath(".//div[@class = 'userinfo']/span[@class = 'location']/text()")[0]
            match = int(div.xpath(".//p[@class = 'match_percentages']/span[@class = 'match']/text()")[0].replace('%', ''))
            friend = int(div.xpath(".//p[@class = 'match_percentages']/span[@class = 'friend']/text()")[0].replace('%', ''))
            enemy = int(div.xpath(".//p[@class = 'match_percentages']/span[@class = 'enemy']/text()")[0].replace('%', ''))
            self.visitors.append(Profile(self._session, name, age, location, match, friend, enemy))
            
    def rate(self, profile, rating):
        """
        Rate a profile 1 through 5 stars. Profile argument may be
        either a Profile object or a string. However, if it is a
        string we must first visit the profile to get its id number.
        Parameters
        ----------
        profile : str or Profile
            The profile that you wish to rate.
        rating : str or int
            1 through 5 star rating that you wish to bestow.
        """
        if isinstance(profile, str):
            profile = self.visit(profile)
        parameters = {
            'target_userid': profile._id,
            'type': 'vote',
            'target_objectid': '0',
            'vote_type': 'personality',
            'score': rating,
            }
        self._session.post('http://www.okcupid.com/vote_handler', data=parameters)
                    
    def __str__(self):
        return '<User {0}>'.format(self.username)
        
class Profile:
    """
    Represent another user on OKCupid. You should not initialize these
    on their own. Instead, User.search() returns a list of Profile
    objects, and User.visit() returns a single Profile object. You can
    also find a list of Profile objects in User.visitors. Most of the
    attributes will be empty until User.visit() is called. 
    self.questions, self.traits, and self.pics will remain empty until
    self.update_questions(), self.update_traits(), and
    self.update_pics() are called, respectively.
    Parameters
    ----------
    name : str
        The username of this profile.
    age : int
        The age of this profile's user.
    location : str
        The geographical location of this profile's user.
    match : int
        The match percentage that you have with this profile.
    friend : int
        The friend percentage that you have with this profile.
    enemy : int
        The enemy percentage that you have with this profile.
    """
    def __init__(self, _session, name, age=None, location='', match=None,
                 friend=None, enemy=None, id=None):
        self._session = _session
        self.name = name
        self.age = age
        self.location = location
        self.match = match
        self.friend = friend
        self.enemy = enemy
        self._id = id
        self.gender = None
        self.orientation = None
        self.status = None
        self.pics = []
        self.questions = []
        self.traits = []
        self.essays = {
            'self summary': '',
            'life': '',
            'good at': '',
            'first things': '',
            'favorites': '',
            'six things': '',
            'thinking': '',
            'friday night': '',
            'private thing': '',
            'message me if': '',
            }
        self.looking_for = {
            'gentation': '',
            'ages': '',
            'near': '',
            'single': '',
            'seeking': '',
            }
        self.details = {
            'last online': '',
            'ethnicity': '',
            'height': '',
            'body type': '',
            'diet': '',
            'smokes': '',
            'drinks': '',
            'drugs': '',
            'religion': '',
            'sign': '',
            'education': '',
            'job': '',
            'income': '',
            'offspring': '',
            'pets': '',
            'speaks': '',
            }
            
    def update_questions(self):
        """
        Update self.questions with Question instances, which contain
        text, answers, user_answer, and explanation attributes. See
        the Question class in objects.py for more details. Like
        User.update_questions(), note that this can take a while due to
        OKCupid displaying only ten questions on each page, potentially
        requiring a large number of requests to the server.
        """
        count = 0
        for category in ['Ethics', 'Sex', 'Religion', 'Lifestyles', 'Dating', 'Other']:
            keep_going = True
            while keep_going:
                questions_data = {
                    'low': 1 + 10*count,
                    category: '1',
                    }
                questions_request = self._session.post('http://www.okcupid.com/profile/{0}/questions'.format(self.name), data=questions_data)
                tree = html.fromstring(questions_request.content.decode('utf8'))
                for div in tree.iter('div'):
                    if 'id' in div.attrib and re.match(r'question_(\d+)', div.attrib['id']):
                        explanation = ''
                        number = re.match(r'question_(\d+)', div.attrib['id']).group(1)
                        text = helpers.replace_chars(div.xpath(".//p[@class = 'qtext']")[0].text)
                        answer_eles = div.xpath(".//input[contains(@id,'question_{0}_qans')]".format(number))
                        answers = []
                        for ele in answer_eles:
                            answers.append(ele.attrib['value'])
                        user_answer_ele = div.xpath(".//span[@id = 'answer_viewer_{0}']".format(number))[0]
                        user_answer = user_answer_ele.text.strip()
                        they_approve = None
                        if 'class' in user_answer_ele.attrib and user_answer_ele.attrib['class'] == 'not_accepted':
                            they_approve = False
                        elif len(user_answer):
                            they_approve = True
                        answer_target = div.xpath(".//span[@id = 'answer_target_{0}']".format(number))[0]
                        you_approve = None
                        if 'class' in answer_target.attrib and answer_target.attrib['class'] == 'not_accepted':
                            you_approve = False
                        elif len(user_answer):
                            you_approve = True                    
                        explanation = div.xpath(".//span[@id = 'note_target_{0}']".format(number))[0].text
                        if explanation is None:
                            explanation = ''
                        else:
                            explanation = helpers.replace_chars(explanation.strip())
                        if text not in [q.text for q in self.questions]:
                            self.questions.append(ProfileQuestion(text,
                                                                  answers,
                                                                  user_answer,
                                                                  explanation,
                                                                  self,
                                                                  category,
                                                                  you_approve,
                                                                  they_approve))
                next = tree.xpath("//a[text() = 'Next']")
                if not len(next) or 'href' not in next[0].attrib:
                    keep_going = False
                else:
                    count += 1
                
    def update_traits(self):
        """
        Fill `self.traits` the personality traits of this profile.
        """
        get_traits = self._session.get('http://www.okcupid.com/profile/{0}/personality'.format(self.name))
        tree = html.fromstring(get_traits.content.decode('utf8'))
        self.traits = tree.xpath("//div[@class = 'pt_row']//label/text()")
    
    def update_pics(self):
        """
        Fill `self.pics` with url strings of pictures for this profile.
        """
        pics_request = self._session.get('http://www.okcupid.com/profile/{0}/photos?cf=profile'.format(self.name))
        pics_tree = html.fromstring(pics_request.content.decode('utf8'))
        self.pics = pics_tree.xpath("//div[@id = 'album_0']//img/@src")
        
    def __repr__(self):
        return '<Profile of {0}>'.format(self.name)
