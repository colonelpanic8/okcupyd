import os
import re
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pyokc",
    version = "0.1.0",
    packages = find_packages(),
    install_requires = ['lxml', 'requests'],

    package_data = {
        '': ['*.md', '*.rst']
    },

    # metadata for upload to PyPI
    author = "Evan Fredericksen",
    author_email = "evfredericksen@gmail.com",
    description = "A framework for interacting with OKCupid.com",
    license = "MIT",
    keywords = "python okcupid",
    url = "http://github.com/pyokc",
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)