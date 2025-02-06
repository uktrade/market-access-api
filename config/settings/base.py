import os
import ssl
import sys
from pathlib import Path

import dj_database_url
import environ
import sentry_sdk
from celery.schedules import crontab
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.utility import is_copilot
from django.core.exceptions import ImproperlyConfigured
from django_log_formatter_asim import ASIMFormatter
from django_log_formatter_ecs import ECSFormatter
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = Path(__file__).parents[2]

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

env = environ.Env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# As app is running behind a host-based router supplied by Heroku or other
# PaaS, we can open ALLOWED_HOSTS
ALLOWED_HOSTS = ["*"]

DEBUG = env.bool("DEBUG", False)
SSO_ENABLED = env.bool("SSO_ENABLED", True)

ELASTIC_APM_ENABLED = env.bool("ELASTIC_APM_ENABLED", default=not DEBUG)

if ELASTIC_APM_ENABLED:
    ELASTIC_APM = {
        "SERVICE_NAME": "market-access-api",
        "SECRET_TOKEN": env("ELASTIC_APM_SECRET_TOKEN"),
        "SERVER_URL": env("ELASTIC_APM_URL"),
        "ENVIRONMENT": env("ENVIRONMENT", default="dev"),
    }

# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_celery_beat",
    "django_extensions",
    "django_filters",
    "hawkrest",
    "oauth2_provider",
    "rest_framework",
    "simple_history",
    "ordered_model",
    "django_audit_log_middleware",
]

LOCAL_APPS = [
    "api.action_plans",
    "api.assessment",
    "api.barrier_downloads",
    "api.barriers",
    "api.collaboration",
    "api.commodities",
    "api.core",
    "api.dashboard",
    "api.dataset",
    "api.documents",
    "api.feedback",
    "api.healthcheck",
    "api.history",
    "api.interactions",
    "api.metadata",
    "api.pingdom",
    "api.related_barriers",
    "api.user",
    "api.user_event_log",
    "api.wto",
    "authbroker_client",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

if ELASTIC_APM_ENABLED:
    INSTALLED_APPS.append("elasticapm.contrib.django")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "hawkrest.middleware.HawkResponseMiddleware",
    "api.user.middleware.UserActivityLogMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django_audit_log_middleware.AuditLogMiddleware",
    "api.core.middleware.sentry.SentryUserContextMiddleware",
    "api.core.middleware.policy_headers.DisableClientCachingMiddleware",
    "api.core.middleware.policy_headers.SetPermittedCrossDomainPolicyHeaderMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

SENTRY_DSN = env.str("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = env.str("SENTRY_ENVIRONMENT", "")
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", 0.0)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
    )

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
if is_copilot():
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url_from_env("DATABASE_ENV_VAR_KEY")
        )
    }
else:
    DATABASES = {"default": dj_database_url.config(env="DATABASE_URL", default="")}

HASHID_FIELD_SALT = env("DJANGO_HASHID_FIELD_SALT")
HASHID_FIELD_ALLOW_INT_LOOKUP = False

AUTH_USER_MODEL = "auth.User"

# django-oauth-toolkit settings
AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
]

VCAP_SERVICES = env.json("VCAP_SERVICES", default={})

CHAR_FIELD_MAX_LENGTH = 255
REF_CODE_LENGTH = env.int("REF_CODE_LENGTH", 3)
REF_CODE_MAX_TRIES = env.int("REF_CODE_MAX_TRIES", 1000)

# DataHub API
DH_METADATA_URL = env("DH_METADATA_URL")
FAKE_METADATA = env.bool("FAKE_METADATA", False)

NOTIFY_API_KEY = env("NOTIFY_API_KEY")
NOTIFY_SAVED_SEARCHES_TEMPLATE_ID = env("NOTIFY_SAVED_SEARCHES_TEMPLATE_ID")
NOTIFY_BARRIER_NOTIFCATION_ID = env("NOTIFY_BARRIER_NOTIFCATION_ID")
NOTIFY_ACTION_PLAN_NOTIFCATION_ID = env("NOTIFY_ACTION_PLAN_NOTIFCATION_ID")
NOTIFY_ACTION_PLAN_USER_SET_AS_OWNER_ID = env("NOTIFY_ACTION_PLAN_USER_SET_AS_OWNER_ID")

NOTIFY_GENERATED_FILE_ID = env("NOTIFY_GENERATED_FILE_ID")
# DMAS Frontend
DMAS_BASE_URL = env("DMAS_BASE_URL")

# Documents
# CACHE / REDIS
if "redis" in VCAP_SERVICES:
    REDIS_BASE_URL = VCAP_SERVICES["redis"][0]["credentials"]["uri"]
else:
    REDIS_BASE_URL = env("REDIS_BASE_URL", default=None)

if REDIS_BASE_URL:
    REDIS_CACHE_DB = env("REDIS_CACHE_DB", default=0)
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"{REDIS_BASE_URL}/{REDIS_CACHE_DB}",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }

if REDIS_BASE_URL:
    REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=1)
    CELERY_BROKER_URL = f"{REDIS_BASE_URL}/{REDIS_CELERY_DB}"
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    if "rediss://" in REDIS_BASE_URL:
        CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
        CELERY_BROKER_USE_SSL = CELERY_REDIS_BACKEND_USE_SSL

AV_V2_SERVICE_URL = env("AV_V2_SERVICE_URL", default="http://av-service/")

# If we have VCAP_SERVICES then we are running on gov.uk PaaS, let's use the AWS credentials from
# the S3 bucket service binding rather than Vault env vars
if "aws-s3-bucket" in VCAP_SERVICES:
    bucket_credentials = VCAP_SERVICES["aws-s3-bucket"][0]["credentials"]
    default_bucket = {
        "bucket_name": bucket_credentials["bucket_name"],
        "aws_access_key_id": bucket_credentials["aws_access_key_id"],
        "aws_secret_access_key": bucket_credentials["aws_secret_access_key"],
        "aws_region": bucket_credentials["aws_region"],
    }
elif is_copilot():
    default_bucket = {
        "bucket_name": env("DEFAULT_BUCKET", default=""),
        "aws_region": env("AWS_DEFAULT_REGION", default=""),
    }
else:
    default_bucket = {
        "bucket_name": env("DEFAULT_BUCKET", default=""),
        "aws_access_key_id": env("AWS_ACCESS_KEY_ID", default=""),
        "aws_secret_access_key": env("AWS_SECRET_ACCESS_KEY", default=""),
        "aws_region": env("AWS_DEFAULT_REGION", default=""),
    }

S3_BUCKETS = {
    "default": default_bucket,
    "documents": {
        "bucket_name": env("DOCUMENTS_BUCKET", default=""),
        "aws_access_key_id": env("DOCUMENTS_AWS_ACCESS_KEY_ID", default=""),
        "aws_secret_access_key": env("DOCUMENTS_AWS_SECRET_ACCESS_KEY", default=""),
        "aws_region": env("DOCUMENTS_AWS_DEFAULT_REGION", default=""),
    },
}

# ServerSideEncryption
SERVER_SIDE_ENCRYPTION = env("SERVER_SIDE_ENCRYPTION", default="AES256")

# Admin locking
AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = os.environ.get("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = os.environ.get("AUTHBROKER_CLIENT_SECRET")
AUTHBROKER_SCOPES = "read write"

LOGIN_REDIRECT_URL = "/admin/"
RESTRICT_ADMIN = env.bool("RESTRICT_ADMIN", True)
ALLOWED_ADMIN_IPS = os.environ.get("ALLOWED_ADMIN_IPS", "").split(",")
# SECURE_PROXY_SSL_HEADER is needed to force the call back protocall to be https
# setting this effects the Hawk hash generation.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

OAUTH2_PROVIDER = {}

if SSO_ENABLED:
    OAUTH2_PROVIDER["RESOURCE_SERVER_INTROSPECTION_URL"] = env(
        "RESOURCE_SERVER_INTROSPECTION_URL"
    )
    OAUTH2_PROVIDER["RESOURCE_SERVER_AUTH_TOKEN"] = env("RESOURCE_SERVER_AUTH_TOKEN")
    OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INFO_URL"] = env(
        "RESOURCE_SERVER_USER_INFO_URL"
    )
    OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INTROSPECT_URL"] = env(
        "RESOURCE_SERVER_USER_INTROSPECT_URL"
    )
    OAUTH2_PROVIDER["OAUTH2_VALIDATOR_CLASS"] = (
        "api.user.authentication.SSOAuthValidator"
    )

# DRF
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 400,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["api.core.permissions.IsAuthenticated"],
    "SEARCH_PARAM": "q",
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# HAWK settings
HAWK_ID = os.environ.get("HAWK_ID")
DATAHUB_HAWK_ID = os.environ.get("DH_HAWK_ID")
DATA_WORKSPACE_HAWK_ID = os.environ.get("DATA_WORKSPACE_HAWK_ID")

HAWK_CREDENTIALS = {
    HAWK_ID: {
        "id": HAWK_ID,
        "key": os.environ.get("HAWK_KEY"),
        "algorithm": os.environ.get("HAWK_ALGORITHM", "sha256"),
    },
    DATAHUB_HAWK_ID: {
        "id": DATAHUB_HAWK_ID,
        "key": os.environ.get("DH_HAWK_KEY"),
        "algorithm": os.environ.get("DH_HAWK_ALGORITHM", "sha256"),
    },
    DATA_WORKSPACE_HAWK_ID: {
        "id": DATA_WORKSPACE_HAWK_ID,
        "key": os.environ.get("DATA_WORKSPACE_HAWK_KEY"),
        "algorithm": os.environ.get("DATA_WORKSPACE_HAWK_ALGORITHM", "sha256"),
    },
}

SLACK_WEBHOOK = env("SLACK_WEBHOOK", default="")

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"
LOCAL_TIME_ZONE = "Europe/London"

USE_I18N = True

USE_L10N = True

USE_TZ = True

APPEND_SLASH = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = "/static/"


# Logging
# ============================================
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="info").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "asim_formatter": {"()": ASIMFormatter},
        "ecs_formatter": {"()": ECSFormatter},
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "asim": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,  # noqa F405
            "formatter": "asim_formatter",
        },
        "ecs": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,  # noqa F405
            "formatter": "ecs_formatter",
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,  # noqa F405
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["asim", "ecs", "stdout"],
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),  # noqa F405
    },
    "loggers": {
        "django": {
            "handlers": ["asim", "ecs", "stdout"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),  # noqa F405
            "propagate": False,
        },
        "django.server": {
            "handlers": ["asim", "ecs", "stdout"],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["asim", "ecs", "stdout"],
            "level": os.getenv("DJANGO_DB_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
    },
}

# Django Log Formatter ASIM settings
if is_copilot():
    DLFA_TRACE_HEADERS = ("X-B3-TraceId", "X-B3-SpanId")

CELERY_BEAT_SCHEDULE = {}

if not DEBUG:
    # Runs daily at midnight
    CELERY_BEAT_SCHEDULE["reindex_related_barriers"] = {
        "task": "api.related_barriers.tasks.reindex_related_barriers",
        "schedule": crontab(minute=0, hour=0),
    }

    # Runs daily at 6am
    CELERY_BEAT_SCHEDULE["send_notification_emails"] = {
        "task": "api.user.tasks.send_notification_emails",
        "schedule": crontab(minute=0, hour=6),
    }
    # Runs daily at 6am
    CELERY_BEAT_SCHEDULE["send_barrier_inactivity_reminders"] = {
        "task": "api.barriers.tasks.send_barrier_inactivity_reminders",
        "schedule": crontab(minute=0, hour=6),
    }

    AUTO_ARCHIVE_DORMANT_FUNCTIONALITY_SWITCH = env(
        "AUTO_ARCHIVE_DORMANT_FUNCTIONALITY_SWITCH", default=False
    )
    if AUTO_ARCHIVE_DORMANT_FUNCTIONALITY_SWITCH:
        # Runs monthly at midnight between the 27th and 28th days of the month
        CELERY_BEAT_SCHEDULE["auto_update_inactive_barrier_status"] = {
            "task": "api.barriers.tasks.auto_update_inactive_barrier_status",
            "schedule": crontab(minute=0, hour=0, day_of_month="28"),
        }
        # Runs monthly at midnight on the 1st day of the month
        CELERY_BEAT_SCHEDULE["send_auto_update_inactive_barrier_notification"] = {
            "task": "api.barriers.tasks.send_auto_update_inactive_barrier_notification",
            "schedule": crontab(minute=0, hour=0, day_of_month="1"),
        }


# Public Data for Barriers
# ============================================
# Option flag to turn off publication within the app
PUBLIC_DATA_TO_S3_ENABLED = env("PUBLIC_DATA_TO_S3_ENABLED", default=True)
# Data files are versioned in the following format
# v[MAJOR].[MINOR].[REVISION] - i.e.: v1.0.56
# Should you need to change the structure of the data published
# please adjust the version accordingly
# Note: when you reach 9 with MINOR please bump MAJOR
PUBLIC_DATA_MAJOR = 1
PUBLIC_DATA_MINOR = 0
# Version validation
if PUBLIC_DATA_MINOR > 9:
    raise ImproperlyConfigured("PUBLIC_DATA_MINOR should not be greater than 9")
# AWS S3 Bucket info
PUBLIC_DATA_AWS_ACCESS_KEY_ID = env("PUBLIC_DATA_AWS_ACCESS_KEY_ID")
PUBLIC_DATA_AWS_SECRET_ACCESS_KEY = env("PUBLIC_DATA_AWS_SECRET_ACCESS_KEY")
PUBLIC_DATA_BUCKET = env("PUBLIC_DATA_BUCKET")
PUBLIC_DATA_BUCKET_REGION = env("PUBLIC_DATA_BUCKET_REGION")
PUBLIC_DATA_KEY_PREFIX = env("PUBLIC_DATA_KEY_PREFIX")

FRONTEND_DOMAIN = env("FRONTEND_DOMAIN", default="http://localhost:9880")

DEFAULT_EXPORT_DATE_FORMAT = "%Y-%m-%d"

SEARCH_DOWNLOAD_APPROVAL_NOTIFICATION_ID = env.str(
    "SEARCH_DOWNLOAD_APPROVAL_NOTIFICATION_ID", default=""
)
APPROVED_FOR_BARRIER_DOWNLOADS_GROUP_NAME = "Download approved user"

# Barrier inactivity reminder emails

# After how many days should the user be reminded to update their barrier
BARRIER_INACTIVITY_THRESHOLD_DAYS = 30 * 6

# If barrier stays inactive despite reminder being sent,
# how many days from reminder date should we send the reminder again
BARRIER_REPEAT_REMINDER_THRESHOLD_DAYS = 30 * 6

# After how many days should a barrier be automatically updated to "Dormant" status
BARRIER_INACTIVITY_DORMANT_THRESHOLD_DAYS = 30 * 18

# After how many days should a barrier be automatically updated to "Archived" status
BARRIER_INACTIVITY_ARCHIVE_THRESHOLD_DAYS = 30 * 18

BARRIER_INACTIVITY_REMINDER_NOTIFICATION_ID = env(
    "BARRIER_INACTIVITY_REMINDER_NOTIFICATION_ID", default=""
)

# IDs for the email templates in Notify
# which will be used to inform users that a barriers status as
# a PB100 (priority-barrier-100) has been accepted or rejected
BARRIER_PB100_ACCEPTED_EMAIL_TEMPLATE_ID = env(
    "BARRIER_PB100_ACCEPTED_EMAIL_TEMPLATE_ID", default=""
)
BARRIER_PB100_REJECTED_EMAIL_TEMPLATE_ID = env(
    "BARRIER_PB100_REJECTED_EMAIL_TEMPLATE_ID", default=""
)

# ID for the email templates in Notify
# which will be used to inform regional lead users of barriers
# that will be automatically updated to either "archived" or
# "dormant" within the next month
AUTOMATIC_ARCHIVE_AND_DORMANCY_UPDATE_EMAIL_TEMPLATE_ID = env(
    "AUTOMATIC_ARCHIVE_AND_DORMANCY_UPDATE_EMAIL_TEMPLATE_ID", default=""
)

# ID for the email templates in Notify
# which will be used when a barrier has a new value assessment added
ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID = env(
    "ASSESSMENT_ADDED_EMAIL_TEMPLATE_ID", default=""
)

BARRIER_LIST_DEFAULT_SORT = env.str("BARRIER_LIST_DEFAULT_SORT", default="-reported_on")
