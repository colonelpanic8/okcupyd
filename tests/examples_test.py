import importlib
import os

from . import util


path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')


def build_example_test_function(module_name):
    def function():
        with util.use_cassette('{0}_example'.format(module_name)):
            importlib.import_module('examples.{0}'.format(module_name))
    return function


for root, _, filenames in os.walk(path):
    for filename in filenames:
        try:
            module_name, extention = filename.split('.')
        except:
            continue
        if extention != 'py':
            continue
        function = build_example_test_function(module_name)
        locals()['test_{0}_example'.format(module_name)] = function
