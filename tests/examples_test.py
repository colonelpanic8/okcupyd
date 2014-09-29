import importlib
import os

import mock

from . import util


path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')


def build_example_test_function(module_name):
    @mock.patch('okcupyd.save_file')
    def function(arg):
        with util.use_cassette(cassette_name='{0}_example'.format(module_name)):
            importlib.import_module('examples.{0}'.format(module_name))
    return function


for root, _, filenames in os.walk(path):
    for filename in filenames:
        try:
            module_name, extention = filename.split('.')
        except:
            continue
        if extention != 'py' or module_name == '__init__':
            continue
        function = build_example_test_function(module_name)
        locals()['test_{0}_example'.format(module_name)] = function
