from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SSO_ENABLED = False
HAWK_ENABLED = False

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

INSTALLED_APPS += [
    "api.documents.test.my_entity_document",
]

AV_V2_SERVICE_URL = "http://av-service/"
DOCUMENT_BUCKET = "test-bucket"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
CELERY_TASK_ALWAYS_EAGER = True

# Stop WhiteNoise emitting warnings when running tests without running collectstatic first
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True