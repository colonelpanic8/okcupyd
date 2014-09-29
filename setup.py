import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="okcupyd",
    version="0.5.0",
    packages=['okcupyd'],
    install_requires=['lxml', 'requests >= 2.4.1', 'simplejson',
                      'ipython >= 2.2.0', 'wrapt', 'coloredlogs'],
    tests_require=['tox', 'pytest', 'mock', 'contextlib2', 'vcrpy'],
    package_data={'': ['*.md', '*.rst']},
    author="Ivan Malison",
    author_email="ivanmalison@gmail.com",
    description="A package for interacting with OKCupid.com",
    license="MIT",
    keywords="python okcupid",
    url="https://github.com/IvanMalison/okcupyd",
    long_description=read('README.md'),
    entry_points={"console_scripts": ["okcupyd=okcupyd:parse_args_and_run"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
