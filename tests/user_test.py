from . import util
from pyokc import User
from pyokc import settings


@util.use_cassette('user_no_picture')
def test_handle_no_pictures():
    assert User().username == util.TESTING_USERNAME
