import logging
import os

import vcr


pyokc_vcr = vcr.VCR(match_on=('path', 'method', 'query'))


def cassette_path(cassette_name):
    return os.path.join(os.path.dirname(__file__),
                        'vcr_cassettes', '{0}.yaml'.format(cassette_name))


def use_cassette(cassette_name, *args, **kwargs):
    return pyokc_vcr.use_cassette(cassette_path(cassette_name), *args, **kwargs)


def enable_log(log_name, level=logging.DEBUG):
    log = logging.getLogger(log_name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(name)s  %(asctime)s] %(message)s'))
    handler.setLevel(level)
    log.setLevel(level)
    log.addHandler(handler)
