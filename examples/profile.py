"""Print a random profile from the quickmatch page."""

import okcupyd

u = okcupyd.User()
p = u.quickmatch() # p is an instance of the Profile class

print('Profile of {0}'.format(p.username))
print('{0}: {1}'.format('Gender', p.gender))
print('{0}: {1}'.format('Age', p.age))
print('{0}: {1}'.format('Orientation', p.orientation))
print('{0}: {1}'.format('Location', p.location))
print('{0}: {1}%'.format('Match', p.match_percentage))
print('{0}: {1}%'.format('Enemy', p.enemy_percentage))
print('----------')
print('')

print('Traits')
print('----------')
for trait in p.traits:
    print(trait)
print('')

print('Essays')
print('----------')

print('Looking For')
print('----------')
for category, response in p.looking_for.items():
    print('{0}: {1}'.format(category, response))
print('')

print('Details')
print('----------')
for category, detail in p.details.items():
    print('{0}: {1}'.format(category, detail))
