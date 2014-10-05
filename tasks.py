from invoke import task, run


@task
def pypi():
    run("python setup.py sdist upload -r pypi")


@task(aliases='r')
def rerecord(rest=''):
    run('tox -e py27 -- --record --credentials test_credentials {0}'.format(rest))
    run('tox -e py27 -- --resave --scrub --credentials test_credentials {0}'.format(rest))


@task
def rerecord_failing():
    result = run("tox -e py27 | grep test_ | grep \u2015 | sed 's:\\\u2015::g'",
                 hide='out')
    for test_name in result.stdout.split('\n'):
        rerecord(rest='-k {0}'.format(test_name.strip()))
