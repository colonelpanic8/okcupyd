import copy
import logging
import os
import zlib

from six.moves import urllib
import simplejson
import vcr

from okcupyd import settings
from okcupyd import util

log = logging.getLogger(__name__)

TESTING_USERNAME = 'username'
TESTING_PASSWORD = 'password'
WBITS = 16 + zlib.MAX_WBITS


SHOULD_SCRUB = True
REPLACEMENTS = []
REMOVE_OLD_CASSETTES = False


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
    if urllib.parse.urlsplit(request.uri).path == '/login':
        request.body = scrub_query_string(request.body)
    request.uri = scrub_uri(request.uri)
    return request


def scrub_uri(uri):
    replaced = util.replace_all_case_insensitive(uri, TESTING_USERNAME,
                                                 settings.USERNAME)
    return util.replace_all_case_insensitive(replaced, TESTING_PASSWORD,
                                             settings.PASSWORD)


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
    if isinstance(incoming, str) and bytes is not str:
        incoming = bytes(incoming, 'utf8')
    else:
        incoming = incoming.encode('utf8')
    compress_object = zlib.compressobj(6, zlib.DEFLATED, WBITS)
    start = compress_object.compress(incoming)
    end = compress_object.flush()
    if not isinstance(start, str):
        return start + end
    return ''.join([start, end])


def scrub_login_response(response):
    if not SHOULD_SCRUB:
        return response
    response = response.copy()
    for item in ('location', 'Location'):
        if item in response['headers']:
            response['headers'][item] = [scrub_uri(uri)
                                         for uri in response['headers'][item]]
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
                             remove_headers(headers_to_remove=('Set-Cookie',
                                                               'Cookie')))


def match_search_query(left, right):
    left_filter = set([value for param_name, value in left.query
                               if 'filter' in param_name])
    right_filter = set([value for param_name, value in right.query
                                if 'filter' in param_name])
    left_rest = set([(param_name, value) for param_name, value in left.query
                     if 'filter' not in param_name])
    right_rest = set([(param_name, value) for param_name, value in right.query
                      if 'filter' not in param_name])

    log.info(simplejson.dumps(
        {
            'filter_differences': list(left_filter.symmetric_difference(right_filter)),
            'rest_differences': list(left_rest.symmetric_difference(right_rest)),
        }
    ))

    return left_filter == right_filter and left_rest == right_rest


def body_as_query_string(left, right):
    try:
        return urllib.parse.parse_qs(left.body) == urllib.parse.parse_qs(right.body)
    except:
        return left.body == right.body


okcupyd_vcr = vcr.VCR(match_on=('path', 'method', 'match_search_query',
                                'body_as_query_string'),
                      before_record=before_record,
                      before_record_response=scrub_login_response,)
okcupyd_vcr.register_matcher('body_as_query_string', body_as_query_string)
okcupyd_vcr.register_matcher('match_search_query', match_search_query)
match_on_no_body = list(filter(lambda x: 'body' not in x, okcupyd_vcr.match_on))



def cassette_path(cassette_name):
    return os.path.join(os.path.dirname(__file__),
                        'vcr_cassettes', '{0}.yaml'.format(cassette_name))

@util.n_partialable
def use_cassette(function=None, cassette_name=None, *args, **kwargs):
    if cassette_name is None:
        assert function, 'Must supply function if no cassette name given'
        cassette_name = function.__name__
    path = cassette_path(cassette_name)
    context_decorator = okcupyd_vcr.use_cassette(path, *args, **kwargs)
    if function:
        return context_decorator(function)
    return context_decorator
