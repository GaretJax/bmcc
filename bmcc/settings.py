import os
import sys
import tempfile
from pathlib import Path

from django.utils.formats import get_format_lazy
from django.utils.translation import gettext_lazy as _

import dj_database_url
import django_cache_url
import psycopg2


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

EXECUTION_MODE = os.environ.get("EXECUTION_MODE", "run")
ENVIRONMENT = os.environ.get("STAGE", "local")


# SECURITY WARNING: keep the secret key used in production secret!
if EXECUTION_MODE == "build":
    SECRET_KEY = "dummy"
else:
    SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "").lower() == "true"

ALLOWED_HOSTS = ["*"]


###############################################################################
# Application definition

INSTALLED_APPS = [
    "adminutils",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    # Third party apps
    "django_celery_results",
    "django_object_actions",
    "import_export",
    "admin_auto_filters",
    # Custom apps
    "bmcc.celery.apps.DefaultConfig",
    "bmcc.missions",
    "bmcc.tracking",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "bmcc.urls"

default_loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "bmcc" / "templates"],
        "OPTIONS": {
            "debug": DEBUG,
            "loaders": default_loaders if DEBUG else cached_loaders,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "bmcc.context_processors.selected_settings",
            ],
        },
    },
]


###############################################################################
# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

if EXECUTION_MODE == "build":
    DATABASES = {}
else:
    DATABASES = {
        "default": dj_database_url.parse(
            os.environ["DEFAULT_DATABASE_DSN"],
            engine="django.contrib.gis.db.backends.postgis",
        )
    }
    DATABASES["default"]["ATOMIC_REQUESTS"] = True
    DATABASES["default"].setdefault("OPTIONS", {}).update(
        {
            "isolation_level": psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ,
        }
    )

    # DATABASES["serializable"] = copy.deepcopy(DATABASES["default"])
    # DATABASES["serializable"].setdefault("OPTIONS", {}).update(
    #     {
    #         "isolation_level": psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE,
    #     }
    # )


###############################################################################
# Cache

if EXECUTION_MODE != "build":
    CACHES = {"default": django_cache_url.parse(os.environ["CACHE_URL"])}
    CACHES["default"].setdefault("OPTIONS", {}).setdefault(
        "MAX_ENTRIES", 999999
    )


###############################################################################
# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


###############################################################################
# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en"

LANGUAGES = [("en", _("English"))]

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True

FORMAT_MODULE_PATH = ["bmcc.formats"]

LOCALE_PATHS = [BASE_DIR / "bmcc" / "locale"]

DATE_INPUT_FORMATS = get_format_lazy("DATE_INPUT_FORMATS")


###############################################################################
# Security (TLS, sessions, cookies,...)

SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "lax"
SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "strict"
CSRF_COOKIE_SECURE = True

USE_X_FORWARDED_PORT = True
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True


###############################################################################
# Celery configuration

CELERY_BEAT_SCHEDULE_FILENAME = os.path.join(
    tempfile.gettempdir(), "celerybeat-schedule"
)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = None  # Never give up
CELERY_BROKER_URL = os.environ.get("BROKER_URL")
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

if ENVIRONMENT == "live":
    CELERY_BEAT_SCHEDULE = {
        # "import_items": {
        # "imp"task": "bmcc.importing.tasks.import_from_active_item_configs",
        # "imp"schedule": timedelta(minutes=1),
        # },
    }


###############################################################################
# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname}/{processName}/{name}.{funcName}:{lineno} {message}",
            "style": "{",
        }
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "simple",
        }
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO"},
        "bmcc": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "aldryn": {"handlers": ["console"], "level": "INFO"},
        "py.warnings": {"handlers": ["console"]},
        "celery": {"handlers": ["console"], "level": "INFO"},
    },
}


###############################################################################
# Storage

PUBLIC_STORAGE_DSN = os.environ.get(
    "PUBLIC_STORAGE_DSN", os.environ.get("DEFAULT_STORAGE_DSN")
)
PRIVATE_STORAGE_DSN = os.environ.get("PRIVATE_STORAGE_DSN")

if ENVIRONMENT == "local":
    MEDIA_ROOT = "/data/"


STATICFILES_DIRS = [BASE_DIR / "bmcc" / "static"]
STATIC_URL = "/static/"
STATIC_ROOT = "/staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "bmcc.storage.DefaultStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        "OPTIONS": {
            "base_url": STATIC_URL,
            "location": STATIC_ROOT,
        },
    },
}

IMPORT_EXPORT_TMP_STORAGE_CLASS = "import_export.tmp_storages.MediaStorage"


###############################################################################
# Sentry

sentry_dsn = os.environ.get("SENTRY_DSN")

if sentry_dsn:
    from sentry_sdk import init
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    init(
        dsn=sentry_dsn,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        debug=DEBUG,
        release=os.environ.get("GIT_COMMIT", "develop"),
        environment=ENVIRONMENT,
        server_name=os.environ.get("DOMAIN", os.environ.get("HOSTNAME")),
        traces_sample_rate=float(
            os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "1.0")
        ),
        profiles_sample_rate=float(
            os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "1.0")
        ),
    )


###############################################################################
# Other settings

FIXTURE_DIRS = ["fixtures"]

ADMIN_SITE_HEADER = os.environ.get("ADMIN_SITE_HEADER", "BMCC")

ANONYMOUS_REDIRECT_URL = os.environ.get(
    "ANONYMOUS_REDIRECT_URL", "admin:index"
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SITE_ID = 1

X_FRAME_OPTIONS = "SAMEORIGIN"

INTERNAL_IPS = ["127.0.0.1"]
