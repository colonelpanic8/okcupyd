"""Print a random profile from the quickmatch page."""

import okcupyd

u = okcupyd.User()
p = u.quickmatch() # p is an instance of the Profile class

print('Profile of {0}'.format(p.username))

print('\n'.join('{0}{1}'.format(title, value)
                for title, value in (('Gender', p.gender),
                                     ('Age', p.age),
                                     ('Orientation', p.orientation),
                                     ('Location', p.location),
                                     ('Match', p.match_percentage),
                                     ('Enemy', p.enemy_percentage))))
