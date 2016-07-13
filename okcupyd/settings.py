"""Module where the default username and password for logging in to
okcupid are housed.
"""
import os
import yaml

#: The username that will be used to log in to okcupid
USERNAME = os.environ.get('OKC_USERNAME')
#: The password that will be used to log in to okcupid
PASSWORD = os.environ.get('OKC_PASSWORD')

AF_USERNAME = os.environ.get('AF_USERNAME', USERNAME)
AF_PASSWORD = os.environ.get('AF_PASSWORD', PASSWORD)

OKCUPYD_CONFIG_FILENAME = '.okcupyd.yml'

def okcupyd_config_at_path(path):
    return os.path.join(path, OKCUPYD_CONFIG_FILENAME)

def generate_paths_to_check():
    yield os.getcwd()
    yield os.path.expanduser("~")


def load_credentials_from_filepath(filepath):
    global USERNAME, PASSWORD
    with open(filepath, 'r') as file_object:
        data = yaml.load(file_object.read())
        USERNAME = data['username']
        PASSWORD = data['password']

    
def load_credentials_from_files():
    for path in generate_paths_to_check():
        filepath = okcupyd_config_at_path(path)
        if os.path.exists(filepath):
            load_credentials_from_filepath(filepath)
            return filepath


if USERNAME is None:
    load_credentials_from_files()
