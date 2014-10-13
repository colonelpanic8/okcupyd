import mock
import pytest

from . import util
from okcupyd.attractiveness_finder import _AttractivenessFinder, AttractivenessFinder


@pytest.fixture
def mock_session():
    return mock.Mock()


@pytest.fixture
def attractiveness_finder(mock_session):
    return _AttractivenessFinder(mock_session)


@mock.patch('okcupyd.attractiveness_finder.search')
def test_attractiveness_finder_stops(mock_search, attractiveness_finder):
    assert attractiveness_finder.find_attractiveness('test_user', accuracy=10000)
    assert mock_search.call_count == 0


@mock.patch('okcupyd.attractiveness_finder.search')
def test_attractiveness_finder(mock_search, attractiveness_finder):
    user_one = 'user_one'
    user_two = 'user_two'
    user_to_attractiveness = {
        user_one: 4875,
        user_two: 9212
    }
    def mock_search_function(session, attractiveness_min=0,
                             attractiveness_max=10000, keywords='', **kwargs):
        if attractiveness_min <= user_to_attractiveness[keywords] <= attractiveness_max:
            return [mock.Mock(username=keywords)]
    mock_search.side_effect = mock_search_function

    user_one_attractiveness = attractiveness_finder(user_one, accuracy=1)
    assert user_one_attractiveness == user_to_attractiveness[user_one]

    user_two_attractiveness = attractiveness_finder.find_attractiveness(user_two,
                                                                        accuracy=1)
    assert user_two_attractiveness == user_to_attractiveness[user_two]

    # Test Rounding
    attractiveness_finder = AttractivenessFinder(mock.Mock())

    assert attractiveness_finder(user_one) == 5000
    assert attractiveness_finder(user_two) == 9000


@pytest.yield_fixture
def cached_attractiveness_finder():
    with util.use_cassette(cassette_name='attractiveness_finder'):
        yield AttractivenessFinder()


@util.use_cassette(cassette_name='attractiveness_finder_live')
def test_attractiveness_finder_live(cached_attractiveness_finder):
    assert cached_attractiveness_finder('dasmitches') == 5000
