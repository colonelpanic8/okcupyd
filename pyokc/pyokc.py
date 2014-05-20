import re
from lxml import html
try:
    from pyokc import helpers
    from pyokc import magicnumbers
    from pyokc.objects import MessageThread, Question, Session
    from pyokc.settings import USERNAME, PASSWORD
except ImportError:
    import helpers
    import magicnumbers
    from objects import MessageThread, Question, Session
    from settings import USERNAME, PASSWORD

class User:
    """
    Represent an OKCupid user. Username and password are only optional
    if you have already filled in your username and password in
    settings.py.
    Parameters
    ----------
    username : str, optional
        The username for your OKCupid account.
    password : str, optional
        The password for your OKCupid account.
    Raises
    ----------
    AuthenticationError
        If you are unable to login with the username and password
        provided.
    """
    def __init__(self, username=USERNAME, password=PASSWORD):
        self.username = username
        self.inbox = []
        self.outbox = []
        self.drafts = []
        self.questions = []
        self.visitors = []
        self._session = Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36'
        }
        credentials = {'username': username, 'password': password}
        helpers.login(self._session, credentials, headers)
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
        smokes : str or list of str, optional
            Smoking habits of profiles returned.
        drinks : str or list of str, optional
            Drinking habits of profiles returned.
        drugs : str or list of str, optional
            Drug habits of profiles returned.
        education : str or list of str, optional
            Highest level of education attained by profiles returned.
        job : str or list of str, optional
            Industry in which the profile users work.
        income : str or list of str, optional
            Income range of profiles returned.
        religion : str or list of str, optional
            Religion of profiles returned.
        offspring : str or list of str, optional
            Whether the profiles returned have or want children.
        pets : str or list of str, optional
            Dog/cat ownership of profiles returned.
        languages : str or list of str, optional
            Languages spoken for profiles returned.
        diet : str or list of str, optional
            Dietary restrictions of profiles returned.
        sign : str or list of str, optional
            Astrological sign of profiles returned.
        ethnicity : str or list of str, optional
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
            'lquery': location,
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
            if isinstance (value, str) and key.lower() not in ('join_date', 'keywords'):
                value = [value]
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
                                     id=info['id'], rating=info['rating'], contacted=info['contacted']))
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
        prfl.match, prfl.enemy = helpers.get_percentages(profile_tree)
        prfl.age, prfl.gender, prfl.orientation, prfl.status = helpers.get_additional_info(profile_tree)
        if len(profile_tree.xpath("//div[@id = 'rating']")):
            prfl.rating = helpers.get_rating(profile_tree.xpath("//div[@id = 'rating']")[0])
        elif len(profile_tree.xpath("//button[@class = 'flatbutton white binary_rating_button like liked']")):
           prfl.rating = 5
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
        keep_going = True
        question_number = 0
        while keep_going:
            questions_data = {
                'low': 1 + question_number,
                }
            get_questions = self._session.post(
            'http://www.okcupid.com/profile/{0}/questions'.format(self.username),
            data=questions_data)
            tree = html.fromstring(get_questions.content.decode('utf8'))
            next_wrapper = tree.xpath("//li[@class = 'next']")
            # Get a list of each question div wrapper, ignore the first because it's an unanswered question
            question_wrappers = tree.xpath("//div[contains(@id, 'question_')]")[1:]
            for div in question_wrappers:
                if not div.attrib['id'][9:].isdigit():
                    question_wrappers.remove(div)
            for div in question_wrappers:
                question_number += 1
                explanation = ''
                text = helpers.replace_chars(div.xpath(".//div[@class = 'qtext']/p/text()")[0])
                user_answer = div.xpath(".//li[contains(@class, 'mine')]/text()")[0]
                explanation_p = div.xpath(".//p[@class = 'value']")
                if explanation_p[0].text is not None:
                    explanation = explanation_p[0].text
                self.questions.append(Question(text, user_answer, explanation))
            if not len(next_wrapper):
                keep_going = False

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
            enemy = int(div.xpath(".//p[@class = 'match_percentages']/span[@class = 'enemy']/text()")[0].replace('%', ''))
            self.visitors.append(Profile(self._session, name, age, location, match, enemy))

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
        self._session.post('http://www.okcupid.com/vote_handler',
                           data=parameters)

    def quickmatch(self):
        '''
        Return an instance of a Profile representing the profile on
        your Quickmatch page.
        Returns
        ----------
        Profile
        '''
        get_quickmatch = self._session.get('http://www.okcupid.com/quickmatch')
        tree = html.fromstring(get_quickmatch.content.decode('utf8'))
        # all of the profile information on the quickmatch page is hidden in
        # a <script> element, meaning that regex is unfortunately necessary
        for script in tree.iter('script'):
            if script.text is not None:
                search_result = re.search(r'[^{]"tuid" : "(\d+)', script.text)
                if search_result is not None:
                    id = search_result.group(1)
                # I'm sorry.
                broad_result = re.search(r'''"location"\s:\s"(.+?)".+
                                             "epercentage"\s:\s(\d{1,2}),\s
                                             "fpercentage"\s:\s(\d{1,2}),\s
                                             "tracking_age"\s:\s(\d{2}).+
                                             "sn"\s:\s"(.+?)",\s
                                             "percentage"\s:\s(\d{1,2})''',
                                             script.text, re.VERBOSE)
                if broad_result is not None:
                    location = broad_result.group(1)
                    enemy = int(broad_result.group(2))
                    friend = int(broad_result.group(3))
                    age = int(broad_result.group(4))
                    username = broad_result.group(5)
                    match = int(broad_result.group(6))
        return Profile(self._session, username, age=age, location=location,
                       match=match, enemy=enemy, id=id)


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
    enemy : int
        The enemy percentage that you have with this profile.
    rating : int
        The rating you gave this profile.
    contacted : bool
        Whether you've contacted this user or not.
    """
    def __init__(self, _session, name, age=None, location='', match=None,
                 enemy=None, id=None, rating=0, contacted=False):
        self._session = _session
        self._id = id
        self.name = name
        self.age = age
        self.location = location
        self.match = match
        self.enemy = enemy
        self.rating = rating
        self.contacted = contacted
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
            'orientation': '',
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
            'relationship type': '',
            'offspring': '',
            'pets': '',
            'speaks': '',
            }

    def update_questions(self):
        """
        Update self.questions with Question instances, which contain
        text, user_answer, and explanation attributes. See
        the Question class in objects.py for more details. Like
        User.update_questions(), note that this can take a while due to
        OKCupid displaying only ten questions on each page, potentially
        requiring a large number of requests to the server.
        """
        keep_going = True
        question_number = 0
        while keep_going:
            questions_data = {
                'low': 1 + question_number,
                }
            get_questions = self._session.post(
            'http://www.okcupid.com/profile/{0}/questions'.format(self.name),
            data=questions_data)
            tree = html.fromstring(get_questions.content.decode('utf8'))
            next_wrapper = tree.xpath("//li[@class = 'next']")
            question_wrappers = tree.xpath("//div[contains(@id, 'question_')]")
            for div in question_wrappers:
                if not div.attrib['id'][9:].isdigit():
                    question_wrappers.remove(div)
            for div in question_wrappers:
                question_number += 1
                explanation = ''
                text = helpers.replace_chars(div.xpath(".//div[@class = 'qtext']/p/text()")[0])
                user_answer = div.xpath(".//span[contains(@id, 'answer_target_')]/text()")[0].strip()
                explanation_span = div.xpath(".//span[@class = 'note']")
                if explanation_span[0].text is not None:
                    explanation = explanation_span[0].text.strip()
                self.questions.append(Question(text, user_answer, explanation))
            if not len(next_wrapper):
                keep_going = False

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
