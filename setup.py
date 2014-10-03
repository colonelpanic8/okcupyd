from setuptools import setup, find_packages


setup(
    name="okcupyd",
    version="0.7.5",
    packages=find_packages(exclude=('tests*', 'examples')),
    install_requires=['lxml', 'requests >= 2.4.1', 'simplejson',
                      'sqlalchemy >= 0.9.0', 'ipython >= 2.2.0',
                      'wrapt', 'coloredlogs >= 0.8', 'invoke >= 0.9'],
    tests_require=['tox', 'pytest', 'mock', 'contextlib2', 'vcrpy', 'six'],
    package_data={'': ['*.md', '*.rst']},
    author="Ivan Malison",
    author_email="ivanmalison@gmail.com",
    description="A package for interacting with OKCupid.com",
    license="MIT",
    keywords="okcupid",
    url="https://github.com/IvanMalison/okcupyd",
    long_description='',
    entry_points={"console_scripts": ["okcupyd=okcupyd:run_invoke"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
