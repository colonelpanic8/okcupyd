import os
import urllib

import mock


def build_response_object(content):
    return mock.Mock(content=content)


def get_file_path_from_url(url):
    return os.path.join(*urllib.parse.urlsplit(url).path.split('/'))


def get_file_path_for_request(url, params=None, path_to_ignored_params=None):
    params = params or {}
    path_to_ignored_params = path_to_ignored_params or {}

    ignored_params = path_to_ignored_params.get(urllib.parse.urlsplit(url).path, ())
    sorted_params = sorted([(k, v) for k, v in params.items()
                            if k not in ignored_params])
    filename = urllib.parse.urlencode(sorted_params) if sorted_params else '__none__'
    filepath = get_file_path_from_url(url)
    return os.path.join('responses', filepath, filename)


def build_mock_session(params_to_ignore=(), overrides=None,
                       path_to_ignored_params=None):
    overrides = {get_file_path_for_request(url, params, params_to_ignore): value
                 for (url, params), value in overrides}
    def mock_get(url, params=None):
        filepath = get_file_path_for_request(url, params_to_ignore)
        if filepath in overrides:
            content = overrides[filepath]
        else:
            with open(filepath, 'rb') as file_object:
                content = bytes(file_object.read(), 'utf8')
        return build_response_object(content)
    return mock.Mock(get=mock.Mock(side_effect=mock_get))


def write_request_to_disk(content, url, *args, **kwargs):
    folder_list = urllib.parse.urlsplit(url).path.split('/')
    folder_list = [f for f in folder_list if f]
    filepath = 'responses'
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    for folder in folder_list:
        filepath = os.path.join(filepath, folder)
        if not os.path.exists(filepath):
            os.makedirs(filepath)

    with open(get_file_path_for_request(url, *args, **kwargs), 'w') as file_object:
        file_object.write(content)
