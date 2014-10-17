from invoke import Collection, task, run

from okcupyd import tasks


ns = Collection()
ns.add_collection(tasks, name='okcupyd')


@ns.add_task
@task(default=True)
def install():
    run("python setup.py install")


@ns.add_task
@task
def pypi():
    run("python setup.py sdist upload -r pypi")


@ns.add_task
@task
def rerecord(rest):
    run('tox -e py27 -- --record --credentials test_credentials {0} -s'
        .format(rest), pty=True)
    run('tox -e py27 -- --resave --scrub --credentials test_credentials {0} -s'
        .format(rest), pty=True)


@ns.add_task
@task(aliases='r')
def rerecord_one(test_name, rest=''):
    run('tox -e py27 -- --record --credentials test_credentials -k {0} -s {1}'
        .format(test_name, rest), pty=True)
    run('tox -e py27 -- --resave --scrub --credentials test_credentials -k {0} -s {1}'
        .format(test_name, rest), pty=True)


@ns.add_task
@task
def failing_test_names():
    run("tox -e py27 | grep test_ | grep \u2015 | sed 's:\\\u2015::g'", pyt=True)

@ns.add_task
@task
def rerecord_failing():
    result = run("tox -e py27 | grep test_ | grep \u2015 | sed 's:\\\u2015::g'",
                 hide='out')
    for test_name in result.stdout.split('\n'):
        rerecord_one(rest=test_name.strip())


linux_dependencies = ('zlib1g-dev', 'libxml2-dev', 'libxslt1-dev', 'python-dev',
                      'libncurses5-dev')
@ns.add_task
@task(aliases=('linux_dep',))
def install_linux_dependencies():
    install_command = 'sudo apt-get install -y'
    for package in linux_dependencies:
        run('{0} {1}'.format(install_command, package), pty=False)
