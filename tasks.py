from invoke import task, run


@task
def pypi():
    run("python setup.py sdist upload -r pypi")
