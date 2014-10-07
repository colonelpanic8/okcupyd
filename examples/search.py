"""Sample script that downloads the profile pictures of all 5'6"-5'8" Buddhists
living in New York, NY who either do not smoke or are trying to quit.
"""
import okcupyd

session = okcupyd.Session.login()
u = okcupyd.User(session)
profiles = u.search(location='new york, ny', religion='buddhist',
                     height_min=66, height_max=68, gentation='everybody',
                     smokes=['no', 'trying to quit'])


for profile in profiles[:2]:
    for photo_info in profile.photo_infos:
        print(photo_info.jpg_uri)
