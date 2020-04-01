from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)
DJANGO_ENV = 'local'

SSO_ENABLED = env.bool("SSO_ENABLED", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {"console": {"level": "DEBUG", "class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

# Celery
# ---------------------------------------------------------------------------
# During local development all tasks will be executed syncronously,
# blocking the processes until the task returns
CELERY_TASK_ALWAYS_EAGER = True
BROKER_URL = "redis://redis:6379/2"
CELERY_RESULT_BACKEND = "redis://redis:6379/3"
