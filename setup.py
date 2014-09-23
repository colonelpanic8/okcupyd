import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="okcupyd",
    version="0.1.0",
    packages=find_packages(),
    install_requires=['lxml', 'requests', 'simplejson'],
    tests_require=['tox', 'pytest', 'mock'],
    package_data={'': ['*.md', '*.rst']},
    author="Ivan Malison",
    author_email="ivanmalison@gmail.com",
    description="A package for interacting with OKCupid.com",
    license="MIT",
    keywords="python okcupid",
    url="https://github.com/IvanMalison/okcupyd",
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
