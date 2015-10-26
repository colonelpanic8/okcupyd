from okcupyd.location import LocationQueryCache

from tests import util


@util.use_cassette
def test_location_cache():
    cache = LocationQueryCache()
    assert cache.get_locid("94109") == 4265540
    assert cache.get_locid("Portland") == 4169518
