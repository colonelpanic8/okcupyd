'''
Sample script that gives a 5-star rating to the profiles of all
24-year-old straight/gay/bi women/men (depending on your
gender/orientation) in Minneapolis who like the show Arrested 
Development.
'''

from pyokc import pyokc

u = pyokc.User()
profiles = u.search(location='minneapolis, mn', keywords='arrested development',
                    age_min=24, age_max=24, number=1000)
for profile in profiles:
    u.rate(profile, 5)