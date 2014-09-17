<h1>pyokc</h1>

pyokc is a Python 3 package for interacting with OKCupid.com that
was inspired by
<a href="http://www.wired.com/wiredscience/2014/01/how-to-hack-okcupid/">this guy</a>
(sort of).

<h2>Installation</h2>

<h3>virtualenv/tox</h3>

Running pyokc is much easier if you have virtualenv and tox installed. They are both available from pypi, so you can simply run

```bash
pip install pyokc
```

if they are not installed on your machine.

Installation can be triggered from tox by running the tox interactive testenv:

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

3. Manually set your username and password in pyokc/settings.py. This method is not recommended because settings.py is a source controlled file and you could accidentally commit your username and password.

<h2>Use</h2>

Running `tox -e interactive` provides an interactive shell with the environment from examples/start.py:

```python
import pyokc
from pyokc.util import enable_log

af = pyokc.AttractivenessFinder()
u = pyokc.User()
```

<h3>Searching profiles</h3>

To search through the user
```python
profile_list = u.search(age_min=26, age_max=32)
```

this will automatically provide certain filters like 'looking for', 'location' and 'radius'.

You can also use the search function directly. Note that this will create a new session.

```python
profile_list = pyokc.search(age_min=26, age_max=32)
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
the Profile class in pyokc.py to get a better idea of what is available to you.

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

u.read(first_thread)

print(first_thread.messages)
```

Because reading each thread requires a request to the server, you must
first pass a MessageThread object as an argument to `User.read()` before
its `messages` attribute will become available.

<h2>Installation</h2>


pyokc has three dependencies: requests and lxml and simplejson.

<b>Note:</b> Windows users will likely run into issues installing lxml. If
this happens, be sure to install the binaries
<a href="http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml">here</a> and then use
pip again.

<h2>FAQ</h2>

<h3>Why is my program going slowly?</h3>

pyokc overrides the `get` and `post` methods of Requests.Session to include a
3-second delay between requests to OKCupid. Hopefully, this will prevent
someone from making too many requests in too short of a timespan and bringing
down the wrath of the OKCupid powers-that-be. This length of time can be
modified by changing the number assigned to `DELAY` in settings.py.

<h3>Why is x/y/z giving me an error message?</h3>

OKCupid updates its site frequently, and it can be difficult to keep up. If you run into an error, feel free to create an issue or send a pull request, and I'll get to it as quickly as possible.
