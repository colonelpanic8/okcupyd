from . import util
from okcupyd import photo


@util.use_cassette('photo_upload')
def test_photo_upload():
    uploader = photo.PhotoUploader('fixtures/image.jpg')
    upload_response_dict = uploader.upload_and_confirm()
    assert int(upload_response_dict['id']) > 0
