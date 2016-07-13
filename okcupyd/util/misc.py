import getpass

import logging
import shutil
import sys

from coloredlogs import ColoredFormatter, HostNameFilter

from okcupyd import settings


DOMAIN = 'www.okcupid.com'
headers = {
    'accept': 'text/javascript, text/html, application/xml, '
    'text/xml, */*',
    'accept-encoding': 'gzip,deflate',
    'accept-language': 'en-US,en;q=0.8',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.okcupid.com',
    'x-prototype-version': 1.7,
    'x-requested-with': 'XMLHttpRequest',
}


def enable_logger(log_name, level=logging.DEBUG):
    log = logging.getLogger(log_name)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        ColoredFormatter(level_styles={'WARNING': dict(color='red')})
    )
    log.addHandler(handler)
    HostNameFilter.install(handler=handler)

    handler.setLevel(level)
    log.setLevel(level)


def get_credentials():
    if not settings.USERNAME:
        input_function = input if sys.version_info.major == 3 else raw_input
        settings.USERNAME = input_function('username: ').strip()
    if not settings.PASSWORD:
        settings.PASSWORD = getpass.getpass('password: ')


def add_command_line_options(add_argument, use_short_options=True):
    """
    :param add_argument: The add_argument method of an ArgParser.
    :param use_short_options: Whether or not to add short options.
    """
    logger_args = ("--enable-logger",)
    credentials_args = ("--credentials",)
    if use_short_options:
        logger_args += ('-l',)
        credentials_args += ('-c',)
    add_argument(*logger_args, dest='enabled_loggers',
                 action="append", default=[],
                 help="Enable the specified logger.")
    add_argument(*credentials_args, dest='credential_files',
                 action="append", default=[],
                 help="Use the specified credentials module to update "
                 "the values in okcupyd.settings.")
    add_argument('--echo', dest='echo', action='store_true', default=False,
                 help="Echo SQL.")


def handle_command_line_options(args):
    """
    :param args: The args returned from an ArgParser
    """
    for enabled_log in args.enabled_loggers:
        enable_logger(enabled_log)
    for credential_file in args.credential_files:
        settings.load_credentials_from_filepath(credential_file)
    if args.echo:
        from okcupyd import db
        db.echo = True
        db.Session.kw['bind'].echo = True
    return args


def save_file(filename, data):
    with open(filename, 'wb') as out_file:
        shutil.copyfileobj(data, out_file)


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


def replace_all_case_insensitive(a_str, sub, replacement):
    segments = []
    last_stop = 0
    for start in find_all(a_str.lower(), sub.lower()):
        segments.append(a_str[last_stop:start])
        segments.append(replacement)
        last_stop = start + len(sub)
    segments.append(a_str[last_stop:])
    return ''.join(segments)
