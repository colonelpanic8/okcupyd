import sys

import mock

import okcupyd


@mock.patch.object(sys, 'argv', ['okcupyd'])
@mock.patch.object(sys, 'exit')
@mock.patch.object(sys, 'exit')
@mock.patch.object(okcupyd, 'start_ipython')
def test_interactive(*args):
    okcupyd.parse_args_and_run()
    with mock.patch.object(sys, 'argv', ['okcupyd', '-v']):
        okcupyd.parse_args_and_run()
