
Getting Started
###############

Installation/Setup
******************

pip/PyPI
========
okcupyd is available for install from PyPI. If you have pip you can simply run:
```bash
pip install okcupyd
```
to make okcupyd available from import in python.

From Source
===========

You can install from source by running the setup.py script included as part of this repository as follows:

```bash
python setup.py install
```

This can be useful if you want to install a version that has not yet been released on PyPI.

Use
===

Interactive

Installing the okcupyd package should add an executable script to a directory in your path that will allow you to type `okcupyd` to enter an interactive ipython shell that has been prepared for use with okcupyd. Before the shell starts, you will be prompted for your username and password.

<h3>Credentials</h3>

If you wish to avoid entering your password each time you start a new session you can do one of the following things:

1. Create a python module (.py file) with your username and password set to the variables USERNAME and PASSWORD respectively. You can start an interactive session with the USERNAME and PASSWORD stored in `my_credentials.py` in the current working directory of the project by running:

```shell
PYTHONPATH=. okcupyd --credentials my_credentials
```

The PYTHONPATH=. at the front of this command is necessary to ensure that the current directory is searched for modules.

2. Set the shell environment variables OKC_USERNAME and OKC_PASSWORD to your username and password respectively. Make sure to export the variables so they are visible in processes started from the shell. You can make a credentials.sh file using the following template

```shell
export OKC_USERNAME='your_username'
export OKC_PASSWORD='your_password'
```

and run source credentials.sh to do this.

<h3>Basic Examples</h3>

All examples in this section assume that the variable u has been initialized as follows:

```python
import okcupyd

u = okcupyd.User()
```

<h4>Searching profiles</h4>

To search through the user
```python
profile_list = u.search(age_min=26, age_max=32)
```

```python
profile_list = okcupyd.search(age_min=26, age_max=32)
```

<h4>Messaging another user</h4>

```python
u.message('foxylady899', 'Do you have a map?')
```

<h4>Rating a profile</h4>

```python
u.get_profile('foxylady899').rate(5)
```

<h4>Mailbox</h4>

```python
first_thread = u.inbox[0]
print(first_thread.messages)
```
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
