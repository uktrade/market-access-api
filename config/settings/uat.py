import sys

from django_log_formatter_ecs import ECSFormatter

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
DJANGO_ENV = "uat"
SSO_ENABLED = True
RELATED_BARRIER_DB_ON = True
