import okcupyd


u = okcupyd.User()
p = u.quickmatch()

# How to use other users questions:
for q in p.questions:
    if 'marijuana' in q.text.lower():
        print(q.text)
        print(q.their_answer)
        if q.their_note and len(q.their_not):
            print(q.their_note)
        print('')
