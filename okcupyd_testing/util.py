import copy
import inspect
import logging
import os
import zlib

from six.moves import urllib
import simplejson
import vcr
import wrapt

from okcupyd import settings
from okcupyd import util


log = logging.getLogger(__name__)

TESTING_USERNAME = 'username'
TESTING_PASSWORD = 'password'
WBITS = 16 + zlib.MAX_WBITS


SHOULD_SCRUB = False
REPLACEMENTS = []
REMOVE_OLD_CASSETTES = False


@wrapt.decorator
def check_should_scrub(function, instance, args, kwargs):
    if SHOULD_SCRUB:
        return function(*args)
    else:
        return args[0] # The request or response


@util.curry
def remove_headers(request, headers_to_remove=()):
    headers = copy.copy(request.headers)
    headers_to_remove = [h.lower() for h in headers_to_remove]
    keys = [k for k in headers if k.lower() in headers_to_remove]
    if keys:
        for k in keys:
            headers.pop(k)
        request.headers = headers
    return request


def scrub_request_body(request):
    if urllib.parse.urlsplit(request.uri).path == '/login':
        request.body = scrub_query_string(request.body)
    request.uri = scrub_uri(request.uri)
    return request


def scrub_uri(uri):
    replaced = util.replace_all_case_insensitive(uri, settings.USERNAME,
                                                 TESTING_USERNAME)
    return util.replace_all_case_insensitive(replaced, settings.PASSWORD,
                                             TESTING_PASSWORD)


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


def scrub_response_headers(response):
    for item in ('location', 'Location'):
        if item in response['headers']:
            response['headers'][item] = [scrub_uri(uri)
                                         for uri in response['headers'][item]]
    return response


def replace_json_fields(body):
    try:
        response_dict = simplejson.loads(body)
    except:
        return body

    if 'screenname' not in response_dict:
        return body
    if response_dict['screenname'] is not None:
        response_dict['screenname'] = TESTING_USERNAME
    response_dict['userid'] = 1
    response_dict['thumbnail'] = ''
    return simplejson.dumps(response_dict)


def scrub_response(response):
    if not SHOULD_SCRUB:
        return response
    response = response.copy()
    response = scrub_response_headers(response)

    body = response['body']['string']
    try:
        body = zlib.decompress(response['body']['string'], WBITS).decode('utf8')
    except:
        should_recompress = False
    else:
        should_recompress = True

    body = replace_json_fields(body)
    body = util.replace_all_case_insensitive(body, settings.USERNAME,
                                             TESTING_USERNAME)

    if should_recompress:
        body = gzip_string(body)
    response['body']['string'] = body
    return response


before_record = check_should_scrub(util.compose(
    scrub_request_body, remove_headers(headers_to_remove=(
        'Set-Cookie',
        'Cookie'
    ))
))


def _maybe_decode(maybe_bytes):
    try:
        return maybe_bytes.decode('utf-8')
    except (AttributeError, UnicodeDecodeError):
        return maybe_bytes


def _match_search_query(left, right):
    left_filter = set([value for param_name, value in left
                       if 'filter' in _maybe_decode(param_name)])
    right_filter = set([value for param_name, value in right
                        if 'filter' in _maybe_decode(param_name)])
    left_rest = set([(param_name, value) for param_name, value in left
                     if 'filter' not in _maybe_decode(param_name)])
    right_rest = set([(param_name, value) for param_name, value in right
                      if 'filter' not in _maybe_decode(param_name)])

    try:
        log.info(simplejson.dumps(
            {
                'filter_differences': list(
                    left_filter.symmetric_difference(right_filter)
                ),
                'rest_differences': list(
                    left_rest.symmetric_difference(right_rest)
                ),
            }, encoding='utf-8'
        ))
    except Exception as e:
        log.warning(e)

    return left_filter == right_filter and left_rest == right_rest


def match_search_query(left, right):
    return _match_search_query(left.query, right.query)


def body_as_query_string(left, right):
    if left.path == right.path and 'ajaxuploader' in left.path:
        return True # We can't seem to handle matching photo uploads likely
        # because of requests internals.
    try:
        left_qs_items = list(urllib.parse.parse_qs(left.body).items())
        right_qs_items = list(urllib.parse.parse_qs(right.body).items())
    except Exception as exc:
        log.debug(exc)
        return left.body == right.body
    else:
        left_qs_items = [(k, tuple(v)) for k, v in left_qs_items]
        right_qs_items = [(k, tuple(v)) for k, v in right_qs_items]
        return _match_search_query(left_qs_items, right_qs_items)


cassette_library_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                          'tests', 'vcr_cassettes')
okcupyd_vcr = vcr.VCR(match_on=('path', 'method', 'match_search_query',
                                'body_as_query_string'),
                      before_record=(before_record,),
                      before_record_response=scrub_response,
                      cassette_library_dir=cassette_library_directory,
                      path_transformer=vcr.VCR.ensure_suffix('.yaml'))
okcupyd_vcr.register_matcher('body_as_query_string', body_as_query_string)
okcupyd_vcr.register_matcher('match_search_query', match_search_query)
match_on_no_body = list(filter(lambda x: 'body' not in x, okcupyd_vcr.match_on))


@wrapt.adapter_factory
def add_request_to_signature(function):
    argspec = inspect.getargspec(function)
    return inspect.ArgSpec(argspec.args + ['request'], argspec.varargs, argspec.keywords, argspec.defaults)


@wrapt.decorator(adapter=add_request_to_signature)
def skip_if_live(function, instance, args, kwargs):
    request = kwargs.pop('request')
    if request.config.getoption('skip_vcrpy'):
        log.debug("Skipping {0} because vcrpy is being skipped.".format(
            function.__name__
        ))
    else:
        return function(*args, **kwargs)


use_cassette = okcupyd_vcr.use_cassette
