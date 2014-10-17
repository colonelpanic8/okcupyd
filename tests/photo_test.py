from . import util
from okcupyd import User, photo


@util.use_cassette(cassette_name='photo_upload',
                   match_on=util.match_on_no_body)
def test_photo_upload():
    uploader = photo.PhotoUploader()
    upload_response_dict = uploader.upload_and_confirm('fixtures/image.jpg')
    assert int(upload_response_dict['id']) > 0


@util.use_cassette(cassette_name='test_photo_delete', match_on=util.match_on_no_body)
def test_photo_delete():
    user = User()
    response_dict = user.photo.upload_and_confirm(user.quickmatch().photo_infos[0])
    before_delete_photos = user.profile.photo_infos
    user.photo.delete(response_dict['id'])
    user.profile.refresh()
    assert len(before_delete_photos) - 1 == len(user.profile.photo_infos)


def test_make_photo_uri_from_https_link():
    photo_info = photo.Info.from_cdn_uri(
        'https://k0.okccdn.com/php/load_okc_image'
        '.php/images/150x150/558x800/0x21/400x421/0'
        '/2254475731855279447.webp?v=2'
    )
    assert photo_info.id == 2254475731855279447
    assert photo_info.thumb_nail_top == 21


@util.use_cassette
def test_photo_info_upload(vcr_live_sleep):
    user = User()
    response = user.photo.upload_and_confirm(user.quickmatch().photo_infos[0])
    vcr_live_sleep(2)
    assert int(response['id']) in [pi.id for pi in user.profile.photo_infos]
