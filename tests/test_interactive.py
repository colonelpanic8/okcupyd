import sys

import mock

import okcupyd


@mock.patch.object(sys, 'argv', ['okcupyd'])
@mock.patch.object(sys, 'exit')
@mock.patch.object(okcupyd.IPython, 'embed')
@mock.patch.object(okcupyd, 'User')
def test_interactive(*args):
    okcupyd.interactive()
    with mock.patch.object(sys, 'argv', ['okcupyd', '-v']):
        okcupyd.interactive()
