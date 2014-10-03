from invoke import task, run


@task
def pypi():
    run("python setup.py sdist upload -r pypi")


@task(aliases='r')
def rerecord(rest=''):
    run('tox -e py27 -- --record --credentials test_credentials {0}'.format(rest))
    run('tox -e py27 -- --resave --scrub --credentials test_credentials {0}'.format(rest))
