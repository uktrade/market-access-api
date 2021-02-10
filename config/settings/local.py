from django.utils.log import DEFAULT_LOGGING

from .base import *

DJANGO_ENV = "local"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            # exact format is not important, this is the minimum information
            "format": "[%(asctime)s] %(name)s %(levelname)5s - %(message)s",
        },
        "django.server": DEFAULT_LOGGING["formatters"]["django.server"],
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "django.server": DEFAULT_LOGGING["handlers"]["django.server"],
    },
    "loggers": {
        # root logger
        "": {
            "level": "WARNING",
            "handlers": ["console"],
        },
        "market-access-python-frontend": {
            "level": DJANGO_LOG_LEVEL,
            "handlers": ["console"],
            # required to avoid double logging with root logger
            "propagate": False,
        },
        "django.server": DEFAULT_LOGGING["loggers"]["django.server"],
    },
}


# Celery
# ---------------------------------------------------------------------------
# During local development all tasks will be executed syncronously,
# blocking the processes until the task returns
CELERY_TASK_ALWAYS_EAGER = True
BROKER_URL = "redis://redis:6379/2"
CELERY_RESULT_BACKEND = "redis://redis:6379/3"
