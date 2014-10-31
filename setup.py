import os

from setuptools import setup, find_packages


version = '0.8.12'


with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as file:
    long_description = file.read()


setup(
    name="okcupyd",
    version=version,
    packages=find_packages(exclude=('tests*', 'examples')),
    install_requires=['lxml', 'requests >= 2.4.1', 'simplejson',
                      'sqlalchemy >= 0.9.0', 'ipython >= 2.2.0',
                      'wrapt', 'coloredlogs >= 0.8', 'invoke >= 0.9',
                      'six >= 1.8.0'],
    tests_require=['tox', 'pytest', 'mock', 'contextlib2', 'vcrpy >= 1.1.2'],
    package_data={'': ['*.md', '*.rst']},
    author="Ivan Malison",
    author_email="ivanmalison@gmail.com",
    description="A package for interacting with okcupid.com",
    license="MIT",
    keywords=["okcupid", "okcupyd", "pyokc", "online dating"],
    url="https://github.com/IvanMalison/okcupyd",
    long_description=long_description,
    entry_points={"console_scripts": ["okcupyd=okcupyd:interactive"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
