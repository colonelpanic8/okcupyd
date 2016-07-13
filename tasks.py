import os

from invoke import Collection, run

from okcupyd import tasks
from okcupyd import settings
from okcupyd.tasks.util import build_task_factory


DEV_DIRECTORY = os.path.dirname(__file__)
CREDENTIALS_FILE = settings.okcupyd_config_at_path(DEV_DIRECTORY)


ns = Collection()
ns.add_collection(tasks, name='okcupyd')
nstask = build_task_factory(ns)


@nstask(default=True)
def install(ctx):
    run("python setup.py install")


@nstask
def pypi(ctx):
    """Upload to pypi"""
    run("python setup.py sdist upload -r pypi")


@nstask
def rerecord(ctx, rest):
    """Rerecord tests."""
    run('tox -e py27 -- --cassette-mode all --record --credentials {0} -s'
        .format(rest), pty=True)
    run('tox -e py27 -- --resave --scrub --credentials test_credentials {0} -s'
        .format(rest), pty=True)


@nstask(aliases='r')
def rerecord_one(ctx, test_name, rest='', pty=False):
    run('tox -e py27 -- --cassette-mode all --record -k {} -s {} --credentials="{}"'
        .format(test_name, rest, CREDENTIALS_FILE), pty=pty)
    run('tox -e py27 -- --resave --scrub -k {} -s {} --credentials="{}"'
        .format(test_name, rest, CREDENTIALS_FILE), pty=pty)


@nstask
def failing_test_names(ctx):
    run("tox -e py27 | grep test_ | grep \u2015 | sed 's:\\\u2015::g'", pty=True)

    
@nstask
def rerecord_failing(ctx):
    result = run("tox -e py27 | grep test_ | grep \u2015 | sed 's:\\\u2015::g'",
                 hide='out')
    for test_name in result.stdout.split('\n'):
        rerecord_one(rest=test_name.strip())


linux_dependencies = ('zlib1g-dev', 'libxml2-dev', 'libxslt1-dev', 'python-dev',
                      'libncurses5-dev')
@nstask(aliases=('linux_dep',))
def install_linux_dependencies(ctx):
    install_command = 'sudo apt-get install -y'
    for package in linux_dependencies:
        run('{0} {1}'.format(install_command, package), pty=False)
