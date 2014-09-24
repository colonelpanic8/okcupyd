import re

from lxml import html

from . import helpers
from . import util
from .messaging import ThreadFetcher
from .profile import Profile
from .search import SearchManager
from .session import Session


class User(object):

    @classmethod
    def with_credentials(cls, username, password):
        return cls(Session.login(username, password))

    def __init__(self, session=None):
        self._session = session or Session.login()
        profile_response = self._session.get('https://www.okcupid.com/profile')
        self._profile_tree = html.fromstring(profile_response.content.decode('utf8'))
        self.age, self.gender, self.orientation, self.status, self.location = helpers.get_additional_info(self._profile_tree)
        self.authcode = helpers.get_authcode(profile_response.content.decode('utf8'))

        self.username = helpers.get_my_username(self._profile_tree)
        self.questions = []
        self.visitors = []

        self._message_sender = helpers.MessageSender(self._session)
        self.inbox = util.Fetchable(ThreadFetcher(self._session, 1))
        self.outbox = util.Fetchable(ThreadFetcher(self._session, 2))
        self.drafts = util.Fetchable(ThreadFetcher(self._session, 4))

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
        thread_id = None
        if not isinstance(username, str):
            username = username.username
        for thread in sorted(set(self.inbox.items + self.outbox.items), key=lambda t: t.date,
                             reverse=True):
            if thread.correspondent.lower() == username.lower():
                thread_id = thread.thread_id
                break

        return self._message_sender.send_message(username, message_text, thread_id=thread_id)


    def search(self, **kwargs):
        count = kwargs.pop('count', 9)
        return self.search_manager(**kwargs).get_profiles(count=count)

    def search_manager(self, **kwargs):
        kwargs.setdefault('gender', self.gender[0])
        kwargs.setdefault('looking_for', helpers.get_looking_for(self.gender,
                                                                 self.orientation))
        kwargs.setdefault('location', self.location)
        kwargs.setdefault('radius', 25)
        return SearchManager(**kwargs)

    def visit(self, username):
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
        profile_request = self._session.post('http://www.okcupid.com/profile/{0}'.format(prfl.username), data=params)
        profile_tree = html.fromstring(profile_request.content.decode('utf8'))
        prfl.match, prfl.enemy = helpers.get_percentages(profile_tree)
        prfl.age, prfl.gender, prfl.orientation, prfl.status, prfl.location = helpers.get_additional_info(profile_tree)
        helpers.update_essays(profile_tree, prfl.essays)
        helpers.update_looking_for(profile_tree, prfl.looking_for)
        helpers.update_details(profile_tree, prfl.details)
        if prfl.id is None:
            prfl.id = helpers.get_profile_id(profile_tree)
        return prfl

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
            'target_userid': profile.id,
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
