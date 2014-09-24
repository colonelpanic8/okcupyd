<h1>okcupyd</h1>
[![Build Status](https://travis-ci.org/IvanMalison/okcupyd.svg?branch=master)](https://travis-ci.org/IvanMalison/okcupyd)

<h2>Installation</h2>

<h3>pip/PyPI</h3>

okcupyd is available for install from PyPI. If you have pip you can simply run:
```bash
pip install okcupyd
```
to make okcupyd available from import in python.

<h3>development</h3>

If you wish to contribute to this project, it is recommended that you use tox to run tests and enter the interactive environment. You can get tox by running

```bash
pip install tox
```

if you do not already have it.

Once you have cloned the project and installed tox, run:

```shell
tox -e interactive
```

This will create a virtualenv that uses the appropriate version of python (python3) and has all dependencies as well as the useful ipython and ipdb libraries installed. This command will put you inside an interactive ipython shell which can be exited with Ctrl-d.

If you want a shell that has direct access to the virtualenv that was created by tox you can run

```shell
source .tox/interactive/bin/activate
```
in your shell.

<h3>Credentials</h3>

`tox -e interactive` will prompt the user for a username and password each time it is executed. If you wish to avoid entering your password each time you start a new session you can do one of the following things:

1. Create a python module with your username and password set to the variables USERNAME and PASSWORD respectively. You can start an interactive session with the USERNAME and PASSWORD stored in `credentials.py` in the root directory of the project by running.

```shell
tox -e interactive -- -c credentials
```

2. Set the environment variables OKC_USERNAME and OKC_PASSWORD to your username and password respectively. Make sure to export the variables so they are visible in processes started from the shell. You can make a credentials.sh file using the following template

```shell
export OKC_USERNAME='your_username'
export OKC_PASSWORD='your_password'
```

and run source credentials.sh to do this.

3. Manually set your username and password in okcupyd/settings.py. This method is not recommended because settings.py is a source controlled file and you could accidentally commit your username and password.

<h2>Use</h2>

Running `tox -e interactive` provides an interactive shell with the environment from examples/start.py:

```python
import okcupyd
from okcupyd.util import enable_log

af = okcupyd.AttractivenessFinder()
u = okcupyd.User()
```

<h3>Searching profiles</h3>

To search through the user
```python
profile_list = u.search(age_min=26, age_max=32)
```

this will automatically provide certain filters like 'looking for', 'location' and 'radius'.

You can also use the search function directly. Note that this will create a new session.

```python
profile_list = okcupyd.search(age_min=26, age_max=32)
```

<h3>Messaging another user</h3>

```python
u.message('foxylady899', 'Do you have a map?')
```

<h3>Visiting a profile</h3>

`u.visit('foxylady899')` or `u.visit(profile_list[0])`

The argument passed to `visit` can either be a string username or a Profile
object. Note that this will cause you to show up in that user's visitors list,
unless you've turned on invisible browsing. Once you have visited a profile, you
should have access to just about every piece of information that is also
available on the website. You can check out the docstrings and source code of
the Profile class in okcupyd.py to get a better idea of what is available to you.

<h3>Rating a profile</h3>

```python
u.rate('foxylady899', 5)
```
<h3>User/Profile questions</h3>

The questions that you or someone else have answered can be accessed as a
list via the `questions` attribute of `User` or `Profile`, respectively.
Because getting this information can involve a time-consuming number of
requests, you must first manually fill this list via the
`User.update_questions()` or `Profile.update_questions()` methods. You
can then access Question information via attributes like `q.text` and
`q.user_answer`.

<h3>Mailbox</h3>

```python
first_thread = u.inbox[0]
print(first_thread.messages)
```