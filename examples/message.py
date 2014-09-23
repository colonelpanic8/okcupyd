'''
Sample script that prints the first message thread in your inbox, and
sends a response message to the sender.
'''

import okcupyd

u = okcupyd.User()
thread = u.inbox[0]
print(thread.messages)
u.message(thread.correspondent, 'Thank you for that highly informative message!')
thread.reply('This is another way to send a message')
