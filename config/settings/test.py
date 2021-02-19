from .base import *

DEBUG = False
DJANGO_ENV = "test"

SSO_ENABLED = True
HAWK_ENABLED = False
FAKE_METADATA = True
AV_V2_SERVICE_URL = "http://av-service/"

# TODO: figure out what this is! :D
INSTALLED_APPS += [
    "tests.documents.my_entity_document",
]

DOCUMENT_BUCKET = "test-bucket"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

# Stop WhiteNoise emitting warnings when running tests without running collectstatic first
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

# Celery
# ---------------------------------------------------------------------------
# During local development all tasks will be executed syncronously,
# blocking the processes until the task returns
CELERY_TASK_ALWAYS_EAGER = True

DMAS_BASE_URL = "https://dummy.market-access.net"


# Public data
# ---------------------------------------------------------------------------
PUBLIC_DATA_TO_S3_ENABLED = False
PUBLIC_DATA_AWS_ACCESS_KEY_ID = "dummy"
PUBLIC_DATA_AWS_SECRET_ACCESS_KEY = "dummy"
