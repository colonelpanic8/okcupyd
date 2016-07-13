import sys

import mock

import okcupyd
from okcupyd import tasks


@mock.patch.object(sys, 'argv', ['okcupyd'])
@mock.patch.object(sys, 'exit')
@mock.patch.object(tasks.IPython, 'embed')
@mock.patch.object(okcupyd, 'User')
def test_interactive(*args):
    okcupyd.interactive()
    with mock.patch.object(sys, 'argv', ['okcupyd', '-l']):
        okcupyd.interactive()
