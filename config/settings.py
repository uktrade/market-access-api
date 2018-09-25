import logging
import os
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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', False)

# As app is running behind a host-based router supplied by Heroku or other
# PaaS, we can open ALLOWED_HOSTS
ALLOWED_HOSTS = ["*"]


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
    "api.reports",
    "api.barriers",
    "api.core",
    "api.ping",
    "api.metadata",
    "api.user",
    'authbroker_client',
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
    'api.core.middleware.AdminIpRestrictionMiddleware',
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
# django-oauth-toolkit settings  -  removed as duplicated below.
# AUTHENTICATION_BACKENDS = (
#     "oauth2_provider.backends.OAuth2Backend",
#     # Uncomment following if you want to access the admin
#     "django.contrib.auth.backends.ModelBackend"
# )

AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
    'django.contrib.auth.backends.ModelBackend',
    'authbroker_client.backends.AuthbrokerBackend',
]

SSO_ENABLED = env.bool("SSO_ENABLED", True)
CHAR_FIELD_MAX_LENGTH = 255
# DataHub API
DH_METADATA_URL = env("DH_METADATA_URL")
FAKE_METADATA = env.bool("FAKE_METADATA", False)
AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
AUTHBROKER_SCOPES = "read write"
LOGIN_REDIRECT_URL = "/admin/"
RESTRICT_ADMIN = env.bool("RESTRICT_ADMIN", True)
ALLOWED_ADMIN_IPS = env.list("ALLOWED_ADMIN_IPS")
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

OAUTH2_PROVIDER = {}

if SSO_ENABLED:
    OAUTH2_PROVIDER["RESOURCE_SERVER_INTROSPECTION_URL"] = env(
        "RESOURCE_SERVER_INTROSPECTION_URL"
    )
    OAUTH2_PROVIDER["RESOURCE_SERVER_AUTH_TOKEN"] = env("RESOURCE_SERVER_AUTH_TOKEN")

# DRF
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication"
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        "api.core.permissions.IsAuthenticated",
    ],
    "ORDERING_PARAM": "sortby",
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
        "algorithm": "sha256"
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = "/static/"

# Logging for development
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True,
            },
            '': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        }
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'handlers': {
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler'
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'stream': sys.stdout
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': True,
            },
            '': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
        }
    }
