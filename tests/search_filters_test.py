from okcupyd.json_search import search_filters


def test_gentation():
    assert set(search_filters.build(
        gentation=['women who like men', 'gay men only']
    )['gentation']) == set(['4', '34'])
