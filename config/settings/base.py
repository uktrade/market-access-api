import logging
import os
import ssl
import sys
import environ

import dj_database_url

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

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

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # drf
    "rest_framework",
    # misc 3rd party
    "django_extensions",
    "hawkrest",
    "raven.contrib.django.raven_compat",
    "simple_history",
    # sso
    "oauth2_provider",
    # local apps
    "api.barriers",
    "api.core",
    "api.ping",
    "api.metadata",
    "api.user",
    "api.documents",
    "api.interactions",
    "api.assessment",
    "api.collaboration",
    "authbroker_client",
    "api.user_event_log",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "hawkrest.middleware.HawkResponseMiddleware",
    "api.core.middleware.AdminIpRestrictionMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
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
RAVEN_CONFIG = {
    "dsn": env("SENTRY_DSN"),
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    # 'release': raven.fetch_git_sha(os.path.dirname(__file__)),
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:////{0}".format(os.path.join(BASE_DIR, "db.sqlite3"))
    )
}

AUTH_USER_MODEL = "auth.User"
# django-oauth-toolkit settings
AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
    "authbroker_client.backends.AuthbrokerBackend",
]

AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
    "authbroker_client.backends.AuthbrokerBackend",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "authbroker_client.backends.AuthbrokerBackend",
]

VCAP_SERVICES = env.json("VCAP_SERVICES", default={})

CHAR_FIELD_MAX_LENGTH = 255
REF_CODE_LENGTH = env.int("REF_CODE_LENGTH", 3)
REF_CODE_MAX_TRIES = env.int("REF_CODE_MAX_TRIES", 1000)
# DataHub API
DH_METADATA_URL = env("DH_METADATA_URL")
FAKE_METADATA = env.bool("FAKE_METADATA", False)

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

# CELERY (it does not understand rediss:// yet so extra work needed)
if REDIS_BASE_URL:
    # REDIS_BASIC_URL == REDIS_BASE_URL without the SSL
    REDIS_BASIC_URL = REDIS_BASE_URL.replace("rediss://", "redis://")
    REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=1)
    CELERY_BROKER_URL = f"{REDIS_BASIC_URL}/{REDIS_CELERY_DB}"
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    if "rediss://" in REDIS_BASE_URL:
        CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
        CELERY_BROKER_USE_SSL = CELERY_REDIS_BACKEND_USE_SSL

AV_V2_SERVICE_URL = env("AV_V2_SERVICE_URL", default="http://av-service/")
DOCUMENT_BUCKET = env("AWS_SECRET_ACCESS_KEY", default="test-bucket")
DOCUMENT_BUCKETS = {
    "default": {
        "bucket": env("DEFAULT_BUCKET", default=""),
        "aws_access_key_id": env("AWS_ACCESS_KEY_ID", default=""),
        "aws_secret_access_key": env("AWS_SECRET_ACCESS_KEY", default=""),
        "aws_region": env("AWS_DEFAULT_REGION", default=""),
    }
}
# ServerSideEncryption
SERVER_SIDE_ENCRYPTION = env("SERVER_SIDE_ENCRYPTION", default="AES256")

# Admin locking
AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
AUTHBROKER_SCOPES = "read write"
LOGIN_REDIRECT_URL = "/admin/"
RESTRICT_ADMIN = env.bool("RESTRICT_ADMIN", True)
ALLOWED_ADMIN_IPS = env.list("ALLOWED_ADMIN_IPS")
# SECURE_PROXY_SSL_HEADER is needed to force the call back protocall to be https
# setting this effects the Hawk hash generation.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

OAUTH2_PROVIDER = {}

if SSO_ENABLED:
    OAUTH2_PROVIDER["RESOURCE_SERVER_INTROSPECTION_URL"] = env(
        "RESOURCE_SERVER_INTROSPECTION_URL"
    )
    OAUTH2_PROVIDER["RESOURCE_SERVER_AUTH_TOKEN"] = env("RESOURCE_SERVER_AUTH_TOKEN")
    OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INFO_URL"] = env("RESOURCE_SERVER_USER_INFO_URL")
    OAUTH2_PROVIDER["RESOURCE_SERVER_USER_INTROSPECT_URL"] = env("RESOURCE_SERVER_USER_INTROSPECT_URL")

# DRF
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 400,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication"
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

HAWK_ENABLED = env.bool("HAWK_ENABLED", True)
HAWK_CREDENTIALS = {
    env("HAWK_ID"): {
        "id": env("HAWK_ID"),
        "key": env("HAWK_KEY"),
        "algorithm": "sha256",
    }
}

SLACK_WEBHOOK = env("SLACK_WEBHOOK", default="")

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = "/static/"
