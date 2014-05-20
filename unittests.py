import unittest
import random
import string
import sys
from pyokc import pyokc

class TestSequenceFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.u1 = pyokc.User(USERNAME1, PASSWORD1)
        cls.u2 = pyokc.User(USERNAME2, PASSWORD2)
        
    def test_search_and_visit(self):
        profiles = self.u1.search(location="New York, NY", number=30,
                                  age_min=25, age_max=30,
                                  looking_for="straight girls only",
                                  status="single", last_online=86400,
                                  religion="agnostic", monogamy="monogamous")
        self.assertTrue(len(profiles) <= 30)
        prev_match_percentage = 100
        for p in profiles[:3]:
            self.assertTrue(prev_match_percentage >= p.match)
            prev_match = p.match
            self.u1.visit(p)
            self.assertTrue(25 <= p.age <= 30)
            self.assertEqual(p.gender, 'Female')
            self.assertEqual(p.orientation, 'Straight')
            self.assertEqual(p.status, 'Single')
            self.assertTrue(p.details['last online'] == 'Online now!' or
                            "Today" in p.details['last online'] or
                            "Yesterday" in p.details['last online'])
            self.assertIn('monogamous', p.details['relationship type'].lower())
   
    def test_rating(self):
        rating = random.choice((0, 5))
        self.u1.rate(self.u2.username, rating)
        p = self.u1.visit(self.u2.username)
        self.assertEqual(rating, p.rating)

    def test_age(self):
        self.assertIsInstance(self.u1.age, int)
        self.assertTrue(18 <= self.u1.age <= 99)
    
    def test_gender(self):
        self.assertIn(self.u1.gender, ['Male', 'Female'])
        
    def test_orientation(self):
        self.assertIn(self.u1.orientation, ['Straight', 'Bisexual', 'Gay'])
        
    def test_status(self):
        self.assertTrue(len(self.u1.status) and isinstance(self.u1.status, str))
        
    def test_messaging(self):
        mtext = ''.join(random.choice(string.ascii_letters) for i in range(30))
        self.u1.message(self.u2.username, mtext)
        self.u1.update_mailbox('outbox', pages=1)
        m1 = self.u1.outbox[0]
        self.u1.read(m1)
        self.assertEqual(m1.messages[0][4:], mtext)
        

if __name__ == '__main__':
    if len(sys.argv) < 5:
        sys.exit("ERROR: Two usernames/passwords must be supplied for these tests")
    USERNAME1 = sys.argv[1]
    PASSWORD1 = sys.argv[2]
    USERNAME2 = sys.argv[3]
    PASSWORD2 = sys.argv[4]
    del sys.argv[1:5]
    unittest.main()