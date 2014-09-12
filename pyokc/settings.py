import os


USERNAME = os.environ.get('OKC_USERNAME')
PASSWORD = os.environ.get('OKC_PASSWORD')

AF_USERNAME = os.environ.get('AF_USERNAME') or USERNAME
AF_PASSWORD = os.environ.get('AF_PASSWORD') or PASSWORD
DELAY = 0
