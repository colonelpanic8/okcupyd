"""Module where the default username and password for logging in to
okcupid are housed.
"""
import os

#: The username that will be used to log in to okcupid
USERNAME = os.environ.get('OKC_USERNAME')
#: The password that will be used to log in to okcupid
PASSWORD = os.environ.get('OKC_PASSWORD')

AF_USERNAME = os.environ.get('AF_USERNAME', USERNAME)
AF_PASSWORD = os.environ.get('AF_PASSWORD', PASSWORD)
