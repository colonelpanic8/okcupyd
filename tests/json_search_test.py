import pytest

from okcupyd import json_search

from tests import util


@util.use_cassette
def test_basic_json_search():
    for profile in json_search.SearchFetchable()[:4]:
        assert profile.username
        assert profile.details.status
