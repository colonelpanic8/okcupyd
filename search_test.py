from pyokc.pyokc import User
from pyokc.search import Search

expected_request = {'filter2': ['2,27,27'],
                    'sort_type': ['0'],
                    'timekey': ['1'],
                    'mygender': ['m'],
                    'fromWhoOnline': ['0'],
                    'locid': ['0'],
                    'matchOrderBy': ['MATCH'],
                    'filter1': ['0,63'],
                    'count': ['18'],
                    'custom_search': ['0'],
                    'update_prefs': ['1'],
                    'filter3': ['1,1'],
                    'sa': ['1'],
                    'keywords': ['c4llisto']}

for item in expected_request:
    expected_request[item] = expected_request[item][0]

if __name__ == '__main__':
    ivan = User()
    print(expected_request)
    actual_request = Search(keywords='c4llisto', age_min=27, age_max=27, looking_for='everybody').build_search_parameters(ivan._session)
    print(actual_request)
    print(set(expected_request.keys()).symmetric_difference(actual_request.keys()))
    print(ivan.search(age_min=27, age_max=27))
