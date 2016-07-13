from invoke import task

from okcupyd.util import curry


def build_task_factory(ns):
    @curry
    def task_decorator(function, **kwargs):
        name = kwargs.pop("name", None)
        default = kwargs.pop("default", None)
        created_task = task(function, **kwargs)
        ns.add_task(created_task, name=name, default=default)
        return created_task
    return task_decorator
