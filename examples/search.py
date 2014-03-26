'''
Sample script that downloads the profile pictures of all 5'6"-5'8" Buddhists
living in New York, NY who either do not smoke or are trying to quit.
'''

from shutil import copyfileobj
from requests import get
from pyokc import pyokc

u = pyokc.User()
profiles = u.search(location='new york, ny', religion='buddhist',
                    height_min=66, height_max=68, looking_for='everybody',
                    smokes=['no', 'trying to quit'], number=1000)
for profile in profiles:
    u.visit(profile, update_pics=True) # you can also ignore the update_pics kwarg and later call profile.update_pics() 
    print("Downloading {0}'s pictures...".format(profile.name))
    for count, url in enumerate(profile.pics, start=1):
        extension = url.split('.')[-1]
        response = get(url, stream=True)
        with open('{0}{1}.{2}'.format(profile.name, count, extension), 'wb') as out_file:
            copyfileobj(response.raw, out_file)
        del response