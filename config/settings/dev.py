import sys
from .base import *

from django_log_formatter_ecs import ECSFormatter

# SECURITY WARNING: don't run with debug turned on in production!
DJANGO_ENV = 'dev'
SSO_ENABLED = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "ecs_formatter": {
            "()": ECSFormatter,
        },
    },
    "handlers": {
        "ecs": {
            "formatter": "ecs_formatter",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "": {
            "handlers": ["ecs"],
            "level": DJANGO_LOG_LEVEL
        }
    },
}
