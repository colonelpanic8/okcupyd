
from okcupyd import json_search

from tests import util


@util.use_cassette
def test_basic_json_search():
    for profile in json_search.SearchFetchable()[:4]:
        assert profile.username
        assert profile.details.status


@util.use_cassette
def test_order_by_upcasing():
    for profile in json_search.SearchFetchable(order_by='match')[:2]:
        assert profile.username
