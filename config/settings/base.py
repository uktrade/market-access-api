import os
import ssl
import sys
from pathlib import Path

import dj_database_url
import environ
import sentry_sdk
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
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

ELASTIC_APM_ENABLED = env("ELASTIC_APM_ENABLED", default=not DEBUG)

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
    "api.barriers",
    "api.core",
    "api.healthcheck",
    "api.metadata",
    "api.user",
    "api.documents",
    "api.interactions",
    "api.assessment",
    "api.collaboration",
    "api.commodities",
    "authbroker_client",
    "api.user_event_log",
    "api.dataset",
    "api.history",
    "api.wto",
    "api.action_plans",
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
    "simple_history.middleware.HistoryRequestMiddleware",
    "django_audit_log_middleware.AuditLogMiddleware",
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

# Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
    )

COMTRADE_DB_HOST = env("COMTRADE_DB_HOST", default="localhost")
COMTRADE_DB_NAME = env(
    "COMTRADE_DB_NAME", default="rdsbroker_a6496fe4_2087_486c_a5ac_ca452e2e1b63"
)
COMTRADE_DB_PORT = env("COMTRADE_DB_PORT", default="9999")
COMTRADE_DB_USER = env("COMTRADE_DB_USER", default="market_access_dev")
COMTRADE_DB_PWORD = env("COMTRADE_DB_PWORD", default="su4aogo1booCeghaic")

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    "default": dj_database_url.config(env="DATABASE_URL", default=""),
    "comtrade": {
        "host": COMTRADE_DB_HOST,
        "database": COMTRADE_DB_NAME,
        "user": COMTRADE_DB_USER,
        "password": COMTRADE_DB_PWORD,
        "port": COMTRADE_DB_PORT,
        "options": "-c search_path=un",  # data in un schema not public schema
    },
}

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

S3_BUCKETS = {
    "default": {
        "bucket_name": env("DEFAULT_BUCKET", default=""),
        "aws_access_key_id": env("AWS_ACCESS_KEY_ID", default=""),
        "aws_secret_access_key": env("AWS_SECRET_ACCESS_KEY", default=""),
        "aws_region": env("AWS_DEFAULT_REGION", default=""),
    },
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
    OAUTH2_PROVIDER[
        "OAUTH2_VALIDATOR_CLASS"
    ] = "api.user.authentication.SSOAuthValidator"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 400,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["api.core.permissions.IsAuthenticated"],
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
HAWK_CREDENTIALS = {}
HAWK_ENABLED = env.bool("HAWK_ENABLED", True)

if HAWK_ENABLED:
    HAWK_ID = os.environ.get("HAWK_ID")
    HAWK_KEY = os.environ.get("HAWK_KEY")
    HAWK_ALGORITHM = os.environ.get("HAWK_ALGORITHM", "sha256")

    DATAHUB_HAWK_ID = os.environ.get("DH_HAWK_ID")
    DATAHUB_HAWK_KEY = os.environ.get("DH_HAWK_KEY")
    DATAHUB_HAWK_ALGORITHM = os.environ.get("DH_HAWK_ALGORITHM", "sha256")

    DATA_WORKSPACE_HAWK_ID = os.environ.get("DATA_WORKSPACE_HAWK_ID")
    DATA_WORKSPACE_HAWK_KEY = os.environ.get("DATA_WORKSPACE_HAWK_KEY")
    DATA_WORKSPACE_HAWK_ALGORITHM = os.environ.get(
        "DATA_WORKSPACE_HAWK_ALGORITHM", "sha256"
    )

    HAWK_CREDENTIALS = {
        HAWK_ID: {"id": HAWK_ID, "key": HAWK_KEY, "algorithm": HAWK_ALGORITHM,},
        DATAHUB_HAWK_ID: {
            "id": DATAHUB_HAWK_ID,
            "key": DATAHUB_HAWK_KEY,
            "algorithm": DATAHUB_HAWK_ALGORITHM,
        },
        DATA_WORKSPACE_HAWK_ID: {
            "id": DATA_WORKSPACE_HAWK_ID,
            "key": DATA_WORKSPACE_HAWK_KEY,
            "algorithm": DATA_WORKSPACE_HAWK_ALGORITHM,
        },
    }

SLACK_WEBHOOK = env("SLACK_WEBHOOK", default="")

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

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

ENABLED_HANDLERS = env.list("ENABLED_LOGGING_HANDLERS", default=["ecs", "stdout"])

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "ecs_formatter": {"()": ECSFormatter,},
        "simple": {"format": "{asctime} {levelname} {message}", "style": "{",},
    },
    "handlers": {
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
        "handlers": ENABLED_HANDLERS,
        "level": os.getenv("ROOT_LOG_LEVEL", "INFO"),  # noqa F405
    },
    "loggers": {
        "django": {
            "handlers": ENABLED_HANDLERS,
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),  # noqa F405
            "propagate": False,
        },
        "django.server": {
            "handlers": ENABLED_HANDLERS,
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ENABLED_HANDLERS,
            "level": os.getenv("DJANGO_DB_LOG_LEVEL", "ERROR"),  # noqa F405
            "propagate": False,
        },
    },
}

CELERY_BEAT_SCHEDULE = {}

if not DEBUG:
    CELERY_BEAT_SCHEDULE["send_notification_emails"] = {
        "task": "api.user.tasks.send_notification_emails",
        "schedule": crontab(minute=0, hour=6),
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
