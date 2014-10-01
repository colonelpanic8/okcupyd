import okcupyd


u = okcupyd.User()
p = u.quickmatch()


for q in p.questions:
    if 'marijuana' in q.text.lower():
        print(q.text)
        print(q.answer)
        if q.explanation and len(q.explanation):
            print(q.explanation)
        print('')
