"""Read the first message in your inbox and reply in two different ways."""

import okcupyd

u = okcupyd.User()
thread = u.outbox[0]
print(thread.messages)
u.message(thread.correspondent, 'Thank you for that highly informative message!')
thread.reply('This is another way to send a message')
