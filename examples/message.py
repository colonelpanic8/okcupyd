'''
Sample script that prints the first message thread in your inbox, and
sends a response message to the sender.
'''

from pyokc import pyokc

u = pyokc.User()
thread = u.inbox[0]
u.read(thread)
print(thread.messages)
u.message(thread.sender, 'Thank you for that highly informative message!')