from django.utils.log import DEFAULT_LOGGING

from .base import *

DJANGO_ENV = "local"

LOGGING = DEFAULT_LOGGING  # we don't care about comprehensive ECS logging for local

MIDDLEWARE.remove(
    "django_audit_log_middleware.AuditLogMiddleware"
)  # we don't care about audit logs for local
MIDDLEWARE.extend(["api.core.middleware.sql_monitor.SqlMonitorMiddleware"])
