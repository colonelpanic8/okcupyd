import time
import logging

from lxml import html
import requests

from . import helpers
from .settings import DELAY, USERNAME, PASSWORD


log = logging.getLogger(__name__)


class Session(requests.Session):

    @classmethod
    def login(cls, username=USERNAME, password=PASSWORD, headers=None):
        session = cls()
        helpers.login(session, {'username': username,
                                 'password': password}, headers)
        return session

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamp = -DELAY

    def _throttle(self):
        while time.clock() - self.timestamp < DELAY:
            time.sleep(.5)
        self.timestamp = time.clock()

    def post(self, *args, **kwargs):
        self._throttle()
        response = super().post(*args, **kwargs)
        response.raise_for_status()
        return response

    def get(self, *args, **kwargs):
        self._throttle()
        response = super().get(*args, **kwargs)
        response.raise_for_status()
        return response


class Question(object):

    def __init__(self, text, user_answer, explanation):
        self.text = text
        self.user_answer = user_answer
        self.explanation = explanation

    def __repr__(self):
        return '<Question: {0}>'.format(self.text)


class Profile(object):
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
    def __init__(self, _session, username, age=None, location='', match=None,
                 enemy=None, id=None, rating=0, contacted=False):
        self._session = _session
        self._id = id
        self.username = username
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
