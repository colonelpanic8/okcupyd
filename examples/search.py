"""
Sample script that downloads the profile pictures of all 5'6"-5'8" Buddhists
living in New York, NY who either do not smoke or are trying to quit.
"""
from requests import get

import okcupyd


u = okcupyd.User()
profiles = u.search(location='new york, ny', religion='buddhist',
                    height_min=66, height_max=68, looking_for='everybody',
                    smokes=['no', 'trying to quit'], count=1)

for profile in profiles:
    print("Downloading {0}'s pictures...".format(profile.username))
    for count, url in enumerate(profile.picture_uris, start=1):
        extension = url.split('.')[-1].split('?')[0]
        response = get(url, stream=True)
        filename = '{0}{1}.{2}'.format(profile.username, count, extension)
        okcupyd.save_file(filename, response.raw)
        del response
