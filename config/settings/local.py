from django.utils.log import DEFAULT_LOGGING

from .base import *

DJANGO_ENV = "local"

# Celery
# ---------------------------------------------------------------------------
# During local development all tasks will be executed syncronously,
# blocking the processes until the task returns
CELERY_TASK_ALWAYS_EAGER = True
BROKER_URL = "redis://redis:6379/2"
CELERY_RESULT_BACKEND = "redis://redis:6379/3"
