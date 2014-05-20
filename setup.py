import os
import re
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pyokc",
    version = "0.2.3",
    packages = find_packages(),
    install_requires = ['lxml', 'requests'],

    package_data = {
        '': ['*.md', '*.rst']
    },

    # metadata for upload to PyPI
    author = "Evan Fredericksen",
    author_email = "evfredericksen@gmail.com",
    description = "A package for interacting with OKCupid.com",
    license = "MIT",
    keywords = "python okcupid",
    url = "https://github.com/evfredericksen/pyokc",
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
