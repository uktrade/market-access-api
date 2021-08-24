import os

import django
from django.conf import settings

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


# `pytest` automatically calls this function once when tests are run.
def pytest_configure():
    settings.DEBUG = False
    settings.COMTRADE_DB_HOST = "comtrade_test_db"
    settings.COMTRADE_DB_PORT = 5432
    settings.COMTRADE_DB_NAME = "comtrade"
    settings.COMTRADE_DB_USER = "comtrade"
    settings.COMTRADE_DB_PWORD = "password"
    settings.COMTRADE_DB_OPTIONS = ""
    django.setup()
