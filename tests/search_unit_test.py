import mock
import simplejson

from okcupyd.search import SearchFetchable2, SearchJSONFetcher


def test_search_manager():
    with open('second_search_response.json', 'r') as file:
        second_response = simplejson.loads(file.read())
    with open('search_response.json', 'r') as file:
        response = simplejson.loads(file.read())`
    with mock.patch.object(SearchJSONFetcher, 'fetch',
                           side_effect=[response, second_resoponse, {}]):
        fetchable = SearchFetchable2(mock.Mock())
        expected_usernames = [response_item['username']
                              for response_item in response['data']]
        expected_usernames += [response_item['username']
                              for response_item in second_response['data']]
        assert expected_username == [profile.username for profile in fetchable]
