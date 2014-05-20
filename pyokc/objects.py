from time import clock, sleep
import requests
try:
    from pyokc.settings import DELAY
except ImportError:
    from settings import DELAY

class Session(requests.Session):
    def __init__(self):
        super().__init__()
        clock()
        self.timestamp = -DELAY
        
    def post(self, *args, **kwargs):
        while clock() - self.timestamp < DELAY:
            pass
        self.timestamp = clock()
        response = super().post(*args, **kwargs)
        response.raise_for_status()
        return response
        
    def get(self, *args, **kwargs):
        while clock() - self.timestamp < DELAY:
            pass
        self.timestamp = clock()
        response = super().get(*args, **kwargs)
        response.raise_for_status()
        return response
        
class MessageThread:
    """
    Represent a sequence of messages between the main user and
    someone else.
    Parameters
    ----------
    self.sender : str
        The username of the other person with whom you are
        communicating.
    self.threadid : str
        A unique threadid assigned by OKCupid.
    self.unread : bool
        True if you have never read this message. False otherwise.
    self.messages : list of str
        List of messages within this thread. Initially empty. Can be
        updated by calling the read() method of the User class.
    """
    def __init__(self, sender, threadid, unread, session, direction):
        self.sender = sender
        self.threadid = threadid
        self.unread = unread
        self.messages = []
        self._direction = direction
                    
    def __repr__(self):
        if self.unread:
            unread_string = 'Unread'
        else:
            unread_string = 'Read'
        return '<{0} message {1} {2}>'.format(unread_string, self._direction, self.sender)
        
class Question:
    def __init__(self, text, user_answer, explanation):
        self.text = text
        self.user_answer = user_answer
        self.explanation = explanation
       
    def __repr__(self):
        return '<Question: {0}>'.format(self.text)