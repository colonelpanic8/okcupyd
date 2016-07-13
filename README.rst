|Latest PyPI version| |Build Status| |Documentation Status| |Join the
chat at https://gitter.im/IvanMalison/okcupyd|

Development Status
==================

okcupyd was broken when okcupid.com released their redesign of their
website which included a change in the way their private api worked.
This was first reported on July 5th by @mosesmc52 in
`#61 <https://github.com/IvanMalison/okcupyd/issues/61>`__, and later by
@dubiousjim in
`#63 <https://github.com/IvanMalison/okcupyd/issues/63>`__. A migration
to this new API is underway, and since
`0f6b8df9905d29bddce6ee9d9978b73d9905f514 <https://github.com/IvanMalison/okcupyd/commit/0f6b8df9905d29bddce6ee9d9978b73d9905f514>`__,
this new code path has been in use. The search functionality does seem
to be working now, but almost all of the filters DO NOT WORK. Work on
getting these filters working can be tracked in
`#70 <https://github.com/IvanMalison/okcupyd/issues/70>`__ and the more
general work for getting okcupyd back to a stable state can be tracked
in `milestone
v1.0.0 <https://github.com/IvanMalison/okcupyd/milestones/v1.0.0>`__.

Alpha Installation
------------------

Because the old version of okcupyd does not work at all, I have released
an alpha version that uses the new private api. You can get this version
using pip by running:

.. code:: bash

    pip install --pre -U okcupyd

Or by explicitly specifying the version you would like to obtain:

.. code:: bash

    pip install okcupyd==1.0.0a5

Please be aware that these alpha builds will likely have many bugs and
they should not be expected to be stable in any way.

Getting Started
===============

Installation/Setup
------------------

pip/PyPI
~~~~~~~~

okcupyd is available for install from PyPI. If you have pip you can
simply run:

.. code:: bash

    pip install okcupyd

to make okcupyd available for import in python.

From Source
~~~~~~~~~~~

You can install from source by running the setup.py script included as
part of this repository as follows:

.. code:: bash

    python setup.py install

This can be useful if you want to install a version that has not yet
been released on PyPI.

From Docker
~~~~~~~~~~~

okcupyd is available on docker (see
https://registry.hub.docker.com/u/imalison/okcupyd/)

If you have docker installed on your machine, you can run

.. code:: bash

    docker run -t -i imalison/okcupyd okcupyd

to get an interactive okcupyd shell.

Use
---

Interactive
~~~~~~~~~~~

Installing the okcupyd package should add an executable script to a
directory in your $PATH that will allow you to type okcupyd into your
shell of choice to enter an interactive ipython shell that has been
prepared for use with okcupyd. Before the shell starts, you will be
prompted for your username and password. This executable script accepts
the flags --enable-logger which enables a logger of the given name, and
--credentials whose action is described below.

It is highly recommended that you use the --enable-logger=requests and
--enable-logger=okcupyd flags if you encounter any problems.

Credentials
~~~~~~~~~~~

If you wish to avoid entering your password each time you start a new
session you can do one of the following things:

1. Create a python module (.py file) with your username and password set
   to the variables USERNAME and PASSWORD respectively. You can start an
   interactive session with the USERNAME and PASSWORD stored in
   my\\\_credentials.py by running

.. code:: bash

    PYTHONPATH=. okcupyd --credentials my_credentials

from the directory that my\_credentials.py is stored in

The PYTHONPATH=. at the front of this command is necessary to ensure
that the current directory is searched for modules.

If you wish to use a version of this library that you have cloned but
not installed, you can use the tox environment venv to do the same thing
with such a version of the code:

.. code:: bash

    PYTHONPATH=. tox -e venv -- okcupyd --credentials my_credentials

2. Set the shell environment variables OKC\\\_USERNAME and
   OKC\\\_PASSWORD to your username and password respectively. Make sure
   to export the variables so they are visible in processes started from
   the shell. You can make a credentials.sh file to do this using the
   following template:

.. code:: bash

    export OKC_USERNAME='your_username'
    export OKC_PASSWORD='your_password'

Simply run source credentials.sh to set the environment variables and
your shell should be properly configured. Note that this approach
requires that the relevant environment variables be set before
okcupyd.settings is imported.

3. Manually override the values in okcupyd/settings.py. This method is
not recommended because it requires you to find the installation
location of the package. Also, If you are working with a source
controlled version, you could accidentally commit your credentials.

Using ``--credentials`` in a custom script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ~okcupyd.util.misc.add\_command\_line\_options and
~okcupyd.util.misc.handle\_command\_line\_options can be used to make a
custom script support the ``--credentials`` and ``--enable-loggers``
command line flags. The interface to these functions is admittedly a
little bit strange. Refer to the example below for details concerning
how to use them:

.. code:: python

    import argparse
    parser = argparse.ArgumentParser()
    util.add_command_line_options(parser.add_argument)
    args = parser.parse_args()
    util.handle_command_line_options(args)

Basic Examples
--------------

All examples in this section assume that the variable u has been
initialized as follows:

.. code:: python

    import okcupyd
    user = okcupyd.User()

Searching profiles
~~~~~~~~~~~~~~~~~~

To search through the user:

.. code:: python

    profiles = user.search(age_min=26, age_max=32)
    for profile in profiles[:10]:
        profile.message("Pumpkins are just okay.")

To search for users that have answered a particular question in a way
that is consistent with the user's preferences for that question:

.. code:: python

    user_question = user.questions.very_important[0]
    profiles = user.search(question=user_question)
    for profile in profiles[:10]:
        their_question = profile.find_question(user_question.id)
        profile.message("I'm really glad that you answered {0} to {1}".format(
            their_question.their_answer, their_question.question.text
        ))

The search functionality can be accessed without a ~okcupyd.user.User
instance:

.. code:: python

    from okcupyd.json_search import SearchFetchable

    for profile in SearchFetchable(attractiveness_min=8000)[:5]:
        profile.message("hawt...")

This is particularly useful if you want to explicitly provide the
session that should be used to search:

.. code:: python

    from okcupyd.session import Session
    from okcupyd.json_search import SearchFetchable

    session = Session.login('username', 'password')
    for profile in SearchFetchable(session=session, attractiveness_min=8000)[:5]:
        profile.message("hawt...")

For more details about what filter arguments can be used with these
search functions, see the doucmentation for
~okcupyd.json\_search.SearchFetchable

Messaging another user
~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    user.message('foxylady899', 'Do you have a map?')
    # This has slightly different semantics; it will not look through the user's
    # inbox for an existing thread.
    user.get_profile('foxylady889').message('Do you have a map?')

Rating a profile
~~~~~~~~~~~~~~~~

.. code:: python

    user.get_profile('foxylady899').rate(5)

Mailbox
~~~~~~~

.. code:: python

    first_thread = user.inbox[0]
    print(first_thread.messages)

Quickmatch, Essays, Looking For, Details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can access the essays, looking for attributes and detail attributes
of a profile very easily

.. code:: python

    profile = user.quickmatch()
    print(profile.essays.self_summary)
    print(profile.looking_for.ages)
    print(profile.details.orientation)

The data for these attributes is loaded from the profile page, but it
should be noted that this page is only loaded on demand, so the first of
these attribute access calls will make an http request.

A logged in user can update their own details using these objects:

.. code:: python

    user.profile.essays.self_summary = "I'm pretty boring."
    user.profile.looking_for.ages = 18, 19
    user.profile.details.ethnicities = ['asian', 'black', 'hispanic']

These assignments will result in updates to the okcupid website. When
these updates happen, subsequent access to any profile attribute will
result in a new http request to reload the profile page.

Fetchable
~~~~~~~~~

Most of the collection objects that are returned from function
invocations in the okcupyd library are instances of
~okcupyd.util.fetchable.Fetchable. In most cases, it is fine to treat
these objects as though they are lists because they can be iterated
over, sliced and accessed by index, just like lists:

.. code:: python

    for question in user.profile.questions:
        print(question.answer.text)

    a_random_question = user.profile.questions[2]
    for question in questions[2:4]:
        print(question.answer_options[0])

However, in some cases, it is important to be aware of the subtle
differences between ~okcupyd.util.fetchable.Fetchable objects and python
lists. ~okcupyd.util.fetchable.Fetchable construct the elements that
they "contain" lazily. In most of its uses in the okcupyd library, this
means that http requests can be made to populate
~okcupyd.util.fetchable.Fetchable instances as its elments are
requested.

The ~okcupyd.profile.Profile.questions ~okcupyd.util.fetchable.Fetchable
that is used in the example above fetches the pages that are used to
construct its contents in batches of 10 questions. This means that the
actual call to retrieve data is made when iteration starts. If you
enable the request logger when you run this code snippet, you get output
that illustrates this fact:

``{.sourceCode .} 2014-10-29 04:25:04 Livien-MacbookAir requests.packages.urllib3.connectionpool[82461] DEBUG "GET /profile/ShrewdDrew/questions?leanmode=1&low=11 HTTP/1.1" 200 None  Yes  Yes  Kiss someone.  Yes.  Yes  Sex.  Both equally  No, I wouldn't give it as a gift.  Maybe, I want to know all the important stuff.  Once or twice a week  2014-10-29 04:25:04 Livien-MacbookAir requests.packages.urllib3.connectionpool[82461] DEBUG "GET /profile/ShrewdDrew/questions?leanmode=1&low=21 HTTP/1.1" 200 None  No.  No  No  Yes  Rarely / never  Always.  Discovering your shared interests  The sun  Acceptable.  No.``

Some fetchables will continue fetching content for quite a long time.
The search fetchable, for example, will fetch content until okcupid runs
out of search results. As such, things like:

.. code:: python

    for profile in user.search():
        profile.message("hey!")

should be avoided, as they are likely to generate a massive number of
requests to okcupid.com.

Another subtlety of the ~okcupyd.util.fetchable.Fetchable class is that
its instances cache its contained results. This means that the second
iteration over okcupyd.profile.Profile.questions in the example below
does not result in any http requests:

.. code:: python

    for question in user.profile.questions:
        print(question.text)

    for question in user.profile.questions:
        print(question.answer)

It is important to understand that this means that the contents of a
~okcupyd.util.fetchable.Fetchable are not guarenteed to be in sync with
okcupid.com the second time they are requested. Calling
~okcupyd.util.fetchable.Fetchable.refresh will cause the
~okcupyd.util.fetchable.Fetchable to request new data from okcupid.com
when its contents are requested. The code snippet that follows prints
out all the questions that the logged in user has answered roughly once
per hour, including ones that are answered while the program is running.

.. code:: python

    import time

    while True:
        for question in user.profile.questions:
            print(question.text)
        user.profile.questions.refresh()
        time.sleep(3600)

Without the call to user.profile.questions.refresh(), this program would
never update the user.profile.questions instance, and thus what would be
printed to the screen with each iteration of the for loop.

Development
-----------

tox
~~~

If you wish to contribute to this project, it is recommended that you
use tox to run tests and enter the interactive environment. You can get
tox by running

.. code:: bash

    pip install tox

if you do not already have it.

Once you have cloned the project and installed tox, run:

.. code:: bash

    tox -e py27

This will create a virtualenv that has all dependencies as well as the
useful ipython and ipdb libraries installed, and run all okcupyds test
suite.

If you want to run a command with access to a virtualenv that was
created by tox you can run

.. code:: bash

    tox -e venv -- your_command

To use the development version of the interactive shell (and avoid any
conflicts with versions installed in site-packages) you would run the
following command:

.. code:: bash

    tox -e venv -- okcupyd

git hooks
~~~~~~~~~

If you plan on editing this file (getting\_started.rst) you must install
the provided git hooks that are included in this repository by running:

.. code:: bash

    bin/create-githook-symlinks.sh

from the root directory of the repository.

.. |Latest PyPI version| image:: https://img.shields.io/pypi/v/okcupyd.svg
   :target: https://pypi.python.org/pypi/okcupyd/
.. |Build Status| image:: https://travis-ci.org/IvanMalison/okcupyd.svg?branch=master
   :target: https://travis-ci.org/IvanMalison/okcupyd
.. |Documentation Status| image:: https://readthedocs.org/projects/okcupyd/badge/?version=latest
   :target: http://okcupyd.readthedocs.org/en/latest/
.. |Join the chat at https://gitter.im/IvanMalison/okcupyd| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/IvanMalison/okcupyd?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
