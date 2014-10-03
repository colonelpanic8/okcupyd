import importlib
import logging

from invoke import Collection, task

from okcupyd.user import User
from okcupyd.profile_copy import Copy


log = logging.getLogger(__name__)
ns = Collection()


def build_copy(source_credentials, dest_credentials):
    source_module = importlib.import_module(source_credentials)
    dest_module = importlib.import_module(dest_credentials)
    source_user = User.with_credentials(source_module.USERNAME,
                                        source_module.PASSWORD)
    dest_user = User.with_credentials(dest_module.USERNAME,
                                      dest_module.PASSWORD)

    return Copy(source_user, dest_user)


for method in Copy.copy_methods:
    @task
    def copy_task(source_credentials, dest_credentials):
        copy = build_copy(source_credentials, dest_credentials)
        getattr(method, copy)()
    ns.add_task(copy_task, name=method)


@ns.add_task
@task(default=True)
def all(source_credentials, dest_credentials):
    log.info(build_copy(source_credentials, dest_credentials).all())
