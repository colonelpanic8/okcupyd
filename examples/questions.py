import okcupyd


u = okcupyd.User()
p = u.quickmatch()


print('Questions for {0}'.format(p.username))
print('----------')
for q in p.questions:
    if 'marijuana' in q.text.lower():
        print(q.text)
        print(q.user_answer)
        if q.explanation and len(q.explanation):
            print(q.explanation)
        print('')
