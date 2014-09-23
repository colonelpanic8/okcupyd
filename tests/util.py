import copy
import os
import urllib
import zlib

import simplejson
import vcr

from okcupyd import settings
from okcupyd import util

TESTING_USERNAME = 'username'
TESTING_PASSWORD = 'password'
WBITS = 16 + zlib.MAX_WBITS


SHOULD_SCRUB = True


@util.n_partialable
def remove_headers(request, headers_to_remove=()):
    if not SHOULD_SCRUB:
        return request
    headers = copy.copy(request.headers)
    headers_to_remove = [h.lower() for h in headers_to_remove]
    keys = [k for k in headers if k.lower() in headers_to_remove]
    if keys:
        for k in keys:
            headers.pop(k)
        request.headers = headers
    return request


def scrub_request_body(request):
    if not SHOULD_SCRUB:
        return request
    if not urllib.parse.urlsplit(request.uri).path == '/login':
        return request
    request.body = scrub_query_string(request.body)
    return request


def scrub_query_string(query_string):
    request_dict = urllib.parse.parse_qs(query_string)
    if 'password' not in request_dict:
        return query_string

    for key in request_dict:
        request_dict[key] = request_dict[key][0]
    request_dict['username'] = TESTING_USERNAME
    request_dict['password'] = TESTING_PASSWORD
    return urllib.parse.urlencode(request_dict)


def gzip_string(incoming):
    if isinstance(incoming, str):
        incoming = bytes(incoming, 'utf8')
    compress_object = zlib.compressobj(wbits=WBITS)
    return compress_object.compress(incoming) + compress_object.flush()


def scrub_login_response(response):
    if not SHOULD_SCRUB:
        return response
    response = response.copy()
    if 'Set-Cookie' in response['headers']:
        del response['headers']['Set-Cookie']
    try:
        decompressed = zlib.decompress(response['body']['string'], WBITS).decode('utf8')
    except:
        return response

    try:
        response_dict = simplejson.loads(decompressed)
    except:
        response['body']['string'] = gzip_string(decompressed.replace(settings.USERNAME, TESTING_USERNAME))
        return response

    if 'screenname' not in response_dict:
        return response
    if response_dict['screenname'] is not None:
        response_dict['screenname'] = TESTING_USERNAME
    response_dict['userid'] = 1
    response_dict['thumbnail'] = ''
    response['body']['string'] = gzip_string(simplejson.dumps(response_dict))
    return response


before_record = util.compose(scrub_request_body,
                             remove_headers(headers_to_remove=('Set-Cookie', 'Cookie')))


def match_search_query(left, right):
    left_filter = set([value for param_name, value in left.query
                               if 'filter' in param_name])
    right_filter = set([value for param_name, value in right.query
                                if 'filter' in param_name])
    left_rest = set([(param_name, value) for param_name, value in left.query
                     if 'filter' not in param_name])
    right_rest = set([(param_name, value) for param_name, value in right.query
                      if 'filter' not in param_name])
    return left_filter == right_filter and left_rest == right_rest


def body_as_query_string(left, right):
    try:
        return urllib.parse.parse_qs(left.body) == urllib.parse.parse_qs(right.body)
    except:
        return left == right


okcupyd_vcr = vcr.VCR(match_on=('path', 'method', 'match_search_query',
                              'body_as_query_string'),
                    before_record=before_record,
                    before_record_response=scrub_login_response,)
okcupyd_vcr.register_matcher('body_as_query_string', body_as_query_string)
okcupyd_vcr.register_matcher('match_search_query', match_search_query)



def cassette_path(cassette_name):
    return os.path.join(os.path.dirname(__file__),
                        'vcr_cassettes', '{0}.yaml'.format(cassette_name))

@util.n_partialable
def use_cassette(cassette_name, *args, **kwargs):
    return okcupyd_vcr.use_cassette(cassette_path(cassette_name), *args, **kwargs)
