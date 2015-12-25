import getpass

import importlib
import logging
import shutil
import sys

from coloredlogs import ColoredFormatter

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
    handler = ColoredFormatter(level_styles={'WARNING': dict(color='red')})
    handler.setLevel(level)
    log.setLevel(level)
    log.addHandler(handler)


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
    add_argument(*credentials_args, dest='credentials_modules',
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
    for credentials_module in args.credentials_modules:
        update_settings_with_module(credentials_module)
    if args.echo:
        from okcupyd import db
        db.echo = True
        db.Session.kw['bind'].echo = True
    return args


def update_settings_with_module(module_name):
    module = importlib.import_module(module_name)
    if hasattr(module, 'USERNAME') and module.USERNAME:
        settings.USERNAME = module.USERNAME
    if hasattr(module, 'PASSWORD') and module.PASSWORD:
        settings.PASSWORD = module.PASSWORD
    if hasattr(module, 'AF_USERNAME') and module.AF_USERNAME:
        settings.AF_USERNAME = module.AF_USERNAME
    if hasattr(module, 'AF_PASSWORD') and module.AF_PASSWORD:
        settings.AF_PASSWORD = module.AF_PASSWORD


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
