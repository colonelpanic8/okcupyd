import importlib
import logging

from invoke import Collection, task

from okcupyd.user import User
from okcupyd.profile_copy import Copy


log = logging.getLogger(__name__)
ns = Collection()


def build_copy(source_credentials_or_username, dest_credentials):
    dest_module = importlib.import_module(dest_credentials)
    dest_user = User.from_credentials(dest_module.USERNAME,
                                      dest_module.PASSWORD)
    try:
        source_module = importlib.import_module(source_credentials_or_username)
    except ImportError:
        source = dest_user.get_profile(source_credentials_or_username)
    else:
        source = User.from_credentials(source_module.USERNAME,
                                       source_module.PASSWORD)

    return Copy(source, dest_user)


def build_copy_task(method):
    @task
    def copy_task(source_credentials, dest_credentials):
        copy = build_copy(source_credentials, dest_credentials)
        getattr(copy, method)()
    ns.add_task(copy_task, name=method)


for method in Copy.copy_methods:
    build_copy_task(method)


@ns.add_task
@task(default=True)
def all(source_credentials, dest_credentials):
    log.info(build_copy(source_credentials, dest_credentials).all())
