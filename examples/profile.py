'''
Sample script that visits a random profile from the quickmatch page,
and prints out most of the information in the profile.
'''

import pyokc

u = pyokc.User()
p = u.quickmatch() # p is an instance of the Profile class
u.visit(p)
p.update_traits() # only necessary for if you want to fill in p.traits

print('Profile of {0}'.format(p.username))
print('{0}: {1}'.format('Gender', p.gender))
print('{0}: {1}'.format('Age', p.age))
print('{0}: {1}'.format('Orientation', p.orientation))
print('{0}: {1}'.format('Location', p.location))
print('{0}: {1}%'.format('Match', p.match))
print('{0}: {1}%'.format('Enemy', p.enemy))
print('----------')
print('')

print('Traits')
print('----------')
for trait in p.traits:
    print(trait)
print('')

print('Essays')
print('----------')
for title, essay in p.essays.items():
    print('{0}: {1}'.format(title, essay))
print('')

print('Looking For')
print('----------')
for category, response in p.looking_for.items():
    print('{0}: {1}'.format(category, response))
print('')

print('Details')
print('----------')
for category, detail in p.details.items():
    print('{0}: {1}'.format(category, detail))
