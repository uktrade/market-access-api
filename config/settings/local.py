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

LOGGING = DEFAULT_LOGGING  # we don't care about comprehensive ECS logging for local

MIDDLEWARE.remove("django_audit_log_middleware.AuditLogMiddleware")  # we don't care about audit logs for local
