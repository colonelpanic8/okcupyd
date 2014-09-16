"""Functions useful in the manual editing of a vcrpy cassette."""
import urllib
import zlib

from vcr.cassette import Cassette
import simplejson

from tests import util


WBITS = 16 + zlib.MAX_WBITS


def get_cassette(cassette_name):
    return Cassette.load(util.cassette_path(cassette_name))


def gzip_string(incoming):
    if isinstance(incoming, str):
        incoming = bytes(incoming, 'utf8')
    compress_object = zlib.compressobj(wbits=WBITS)
    return compress_object.compress(incoming) + compress_object.flush()


def scrub_logins_from_cassette(cassette_name):
    cassette = get_cassette(cassette_name)
    for index, request in enumerate(cassette.requests):
        if urllib.parse.urlsplit(request.uri).path == '/login':
            scrub_request_body(request)
            response = cassette.responses[index]
            response_dict = simplejson.loads(zlib.decompress(response['body']['string'], WBITS))
            response_dict['screenname'] = 'username'
            response_dict['userid'] = 1
            response_dict['thumbnail'] = ''
            response['body']['string'] = gzip_string(simplejson.dumps(response_dict))
    cassette._save(force=True)


def scrub_request_body(request):
    request_dict = urllib.parse.parse_qs(request.body)
    for key in request_dict:
        request_dict[key] = request_dict[key][0]
    request_dict['username'] = 'username'
    request_dict['password'] = 'username'
    request.body = urllib.parse.urlencode(request_dict)
