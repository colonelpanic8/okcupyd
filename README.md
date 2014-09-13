<h1>pyokc</h1>

pyokc is a Python 3 package for interacting with OKCupid.com that
was inspired by
<a href="http://www.wired.com/wiredscience/2014/01/how-to-hack-okcupid/">this guy</a>
(sort of).

<h2>Use</h2>

<h3>First things first</h3>

Go to settings.py and assign your OKCupid profile name to `USERNAME` and your password
to `PASSWORD`. Alternatively, you can store your username and password
in the environment variables OKC_USERNAME and OKC_PASSWORD respectively. From now on you won't need to enter either for any pyokc scripts.

<h3>Starting a new session</h3>

```python
import pyokc

u = pyokc.User()
```

<h3>Messaging another user</h3>

```python
u.message('foxylady899', 'Do you have a map?')
```

<h3>Searching profiles</h3>

```python
profile_list = u.search(age_min=26, age_max=32)
```

Just like OKCupid, pyokc uses default search values if you haven't specified a
particular value. For instance, if you do not state a search location or
radius, the profiles returned will be within a 25-mile radius of your profile's
location. By default, `search` returns 18 profiles, however this can be changed
with the `number` keyword parameter. You can search using every metric that
OKCupid currently allows, with the exception of A-list only options. The
objects returned in the list are Profile objects that contain basic information
about a profile as attributes such as `name`, `age`, and `match`. The actual
content of a profile, however, cannot be accessed without actually visiting the
profile.

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

```bash
pip install pyokc
```

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
