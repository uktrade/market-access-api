from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK" : lambda request: True,
}

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

DEBUG_TOOLBAR_CONFIG = {"JQUERY_URL": ""}

SSO_ENABLED = env.bool("SSO_ENABLED", True)

INTERNAL_IPS = ("127.0.0.1",)

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
