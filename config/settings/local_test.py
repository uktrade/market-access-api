from .base import *

DJANGO_ENV = "local_test"

MIDDLEWARE.remove(
    "django_audit_log_middleware.AuditLogMiddleware"
)  # we don't care about audit logs for local
MIDDLEWARE.extend(["api.core.middleware.sql_monitor.SqlMonitorMiddleware"])

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
