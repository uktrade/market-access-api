import os

from celery import Celery
from dbt_copilot_python.celery_health_check import healthcheck
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("market-access-api")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app = healthcheck.setup(app)

# config sentry
client = Client(
    dsn=os.environ.get("SENTRY_DSN"), environment=os.environ.get("SENTRY_ENVIRONMENT")
)

# register a custom filter to filter out duplicate logs
register_logger_signal(client)

# hook into the Celery error handler
register_signal(client, ignore_expected=True)
