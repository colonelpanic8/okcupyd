import importlib

from invoke import task
from okcupyd import User
from okcupyd import util
from okcupyd.profile_copy import Copy


@task
def copy_questions(source_credentials, dest_credentials):
    source_module = importlib.import_module(source_credentials)
    dest_module = importlib.import_module(dest_credentials)
    source_user = User.with_credentials(source_module.USERNAME,
                                        source_module.PASSWORD)
    dest_user = User.with_credentials(dest_module.USERNAME,
                                      dest_module.PASSWORD)

    Copy(source_user, dest_user).questions()


@task
def enable_logger(logger_name):
    util.enable_logger(logger_name)


@task
def credentials(module_name):
    util.update_settings_with_module(module_name)
