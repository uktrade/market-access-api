import os

import django
from django.conf import settings

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


# `pytest` automatically calls this function once when tests are run.
def pytest_configure():
    settings.DEBUG = False
    settings.COMTRADE_DB_HOST = settings.COMTRADE_TEST_DB_HOST
    settings.COMTRADE_DB_PORT = settings.COMTRADE_TEST_DB_PORT
    settings.COMTRADE_DB_NAME = settings.COMTRADE_TEST_DB_NAME
    settings.COMTRADE_DB_USER = settings.COMTRADE_TEST_DB_USER
    settings.COMTRADE_DB_PWORD = settings.COMTRADE_TEST_DB_PWORD
    settings.COMTRADE_DB_OPTIONS = settings.COMTRADE_TEST_DB_OPTIONS
    django.setup()
