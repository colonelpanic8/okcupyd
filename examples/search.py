"""
Sample script that downloads the profile pictures of all 5'6"-5'8" Buddhists
living in New York, NY who either do not smoke or are trying to quit.
"""
import okcupyd

session = okcupyd.Session.login()
u = okcupyd.User(session)
fetchable = u.search(location='new york, ny', religion='buddhist',
                     height_min=66, height_max=68, looking_for='everybody',
                     smokes=['no', 'trying to quit'])


for profile in fetchable[:1]:
    for count, photo_info in enumerate(profile.photo_infos, start=1):
        url = photo_info.jpg_uri
        extension = url.split('.')[-1].split('?')[0]
        response = session.get(url, stream=True)
        filename = '{0}{1}.{2}'.format(profile.username, count, extension)
        okcupyd.save_file(filename, response.raw)
        del response
