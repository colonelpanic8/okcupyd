import re

from lxml import html

from . import helpers
from . import util
from .objects import MailboxFetcher, Profile, Question, Session
from .search import search
from .xpath import XPathBuilder


class User(object):
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

    @classmethod
    def with_credentials(cls, username, password):
        return cls(Session.login(username, password))

    def __init__(self, session=None):
        self._session = session or Session.login()
        profile_response = self._session.get('https://www.okcupid.com/profile')
        self._profile_tree = html.fromstring(profile_response.content.decode('utf8'))
        self.age, self.gender, self.orientation, self.status, self.location = helpers.get_additional_info(self._profile_tree)
        self.authcode = re.search('var AUTHCODE = "(.*?)";', profile_response.text).group(1)

        self.username = helpers.get_my_username(self._profile_tree)
        self.questions = []
        self.visitors = []

    @util.cached_property
    def inbox(self):
        return list(MailboxFetcher(self._session, 1).get_threads())

    @util.cached_property
    def outbox(self):
        return list(MailboxFetcher(self._session, 2).get_threads())

    @util.cached_property
    def drafts(self):
        return list(MailboxFetcher(self._session, 4).get_threads())

    def update_essay(self, essay_id, essay_body):
        form_data = {
            "essay_id": essay_id,
            "essay_body": essay_body,
            "authcode": self.authcode,
            "okc_api": 1
        }
        self._session.post('https://www.okcupid.com/profileedit2', data=form_data)

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
        return self._session.post('http://www.okcupid.com/mailbox', data=msg_data)

    def search(self, **kwargs):
        kwargs.setdefault('gender', self.gender[0])
        kwargs.setdefault('looking_for', helpers.get_looking_for(self.gender, self.orientation))
        kwargs.setdefault('location', self.location)
        kwargs.setdefault('radius', 25)
        return search(self._session, **kwargs)

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
        question_number = 0
        while True:
            questions_data = {
                'low': 1 + question_number,
            }
            get_questions = self._session.post(
                'http://www.okcupid.com/profile/{0}/questions'.format(self.username),
                data=questions_data)
            tree = html.fromstring(get_questions.content.decode('utf8'))
            next_wrapper = tree.xpath("//li[@class = 'next']")
            # Get a list of each question div wrapper, ignore the first because it's an unanswered question
            question_wrappers = XPathBuilder().div.attribute_contains('id', 'question_').apply_(tree)[1:]
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
                break

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
                    age = int(broad_result.group(4))
                    username = broad_result.group(5)
                    match = int(broad_result.group(6))
        return Profile(self._session, username, age=age, location=location,
                       match=match, enemy=enemy, id=id)


    def __str__(self):
        return '<User {0}>'.format(self.username)
