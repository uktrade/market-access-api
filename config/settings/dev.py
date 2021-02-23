import sys

from django_log_formatter_ecs import ECSFormatter

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DJANGO_ENV = "dev"
SSO_ENABLED = True
