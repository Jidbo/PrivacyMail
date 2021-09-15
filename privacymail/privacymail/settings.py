"""
Django settings for privacymail project.

Generated by 'django-admin startproject' using Django 2.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import sys
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REACT_APP_DIR = os.path.join(BASE_DIR, "website")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv("SECRET_KEY"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("APPLICATION_DEBUG")

ALLOWED_HOSTS = [os.getenv("ALLOWED_HOST")]

MAXIMUM_ALLOWED_EMAIL_ANALYSIS_ONDEMAND = int(os.getenv("MAXIMUM_ALLOWED_EMAIL_ANALYSIS_ONDEMAND"))

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_countries",
    "django_cron",
    "mailfetcher",
    "util",
    "identity",
    "api",
    "django_tables2",
    "django_extensions",
    "django_filters",
    "bootstrap4",
    "whitenoise.runserver_nostatic",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "privacymail.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(REACT_APP_DIR, "build")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "privacymail.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT"),
        "CONN_MAX_AGE": 30,
    }
}

if 'test' in sys.argv:
    DATABASES['default']['PORT'] = 5431


# Caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "pmail_cache",
        "TIMEOUT": None,  # Cache does not automatically expire
        "OPTIONS": {
            "MAX_ENTRIES": 1000000,  # Allow a lot of entries in the cache to avoid culling
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("de", _("German")),
    ("en", _("English")),
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(REACT_APP_DIR, "build", "static")

STATICFILES_DIRS = []

CRON_CLASSES = [
    "mailfetcher.cron.ImapFetcher",
    "mailfetcher.analyser_cron.Analyser",
]

# Specifies a series of URLs to send GET requests to in specific conditions.
# Can be used for monitoring scripts, like healtchecks.io, Dead Man's Snitch, ...
# Structure:
# CRON_WEBHOOKS = {
#     "mailfetcher.cron.ImapFetcher": {
#         "start": None,
#         "fail": None,
#         "success": None,
#     },
#     "mailfetcher.analyser_cron.Analyser": {
#         "start": None,
#         "fail": None,
#         "success": None,
#     }
# }
# Leave any hooks you do not want to use set to None, and add any URLs you want called as strings
# You can also set the entire dictionary to None if you don't want to use this feature.


# CRON_WEBHOOKS = {{ lookup('passwordstore', 'privacymail/cron/webhooks' )}}

OPENWPM_DATA_DIR = os.path.dirname(__file__) + "/tmp/data/"
OPENWPM_LOG_DIR = os.path.dirname(__file__) + "/tmp/log/"

# URL on which the server is reached
SYSTEM_ROOT_URL = "http://{{ pm_domain }}"

# Mail credentials

MAILCREDENTIALS = [
    {
        "MAILHOST": "mail.newsletterme.de",
        "MAILUSERNAME": os.getenv("MAIL_NEWSLETTER_USERNAME"),
        "MAILPASSWORD": os.getenv("MAIL_NEWSLETTER_PASSWORD"),
        "DOMAIN": "newsletterme.de",
    },
    {
        "MAILHOST": "mail.privacyletter.de",
        "MAILUSERNAME": os.getenv("MAIL_PRIVAYCLETTER_USERNAME"),
        "MAILPASSWORD": os.getenv("MAIL_PRIVAYCLETTER_PASSWORD"),
        "DOMAIN": "privacyletter.de",
    },
    {
        "MAILHOST": "mail.privacy-mail.org",
        "MAILUSERNAME": os.getenv("MAIL_PRIVACYMAIL_USERNAME"),
        "MAILPASSWORD": os.getenv("MAIL_PRIVACYMAIL_PASSWORD"),
        "DOMAIN": "privacy-mail.org",
    },
]

DEVELOP_ENVIRONMENT = False
RUN_OPENWPM = True
# Also click one link per mail, to analyze the resulting connection for PII leakages.
# Warning! Detection of unsubscribe links cannot be guaranteed!
VISIT_LINKS = True

# How many links to skip at the beginning and end of a mail, as they may are more likely to be unsubscribe links.
NUM_LINKS_TO_SKIP = 6

# Dictionary of fragments, for which links are scanned to determine, wether they are unsubscribe links.
UNSUBSCRIBE_LINK_DICT = [
    "sub",  # unsubscribe, subscribtion
    "abmelden",  # unsubscribe german
    "stop",
    "rem",  # remove
    "abbes",  # abbestellen german
    "here",  # german
    "hier",  # German
    "annu",  # annulla italian, annuler french
    "canc",  # cancel and cancellarsi italian
    "disdici",  # italian
    "dés",  # french
    "abonn",  # abonn french
    "retiré",  # french
]

# Number of mails to be processed per batch by the cronjob.
CRON_MAILQUEUE_SIZE = 50

# Number of retries
OPENWPM_RETRIES = 3

OPENWPM_TIMEOUT = 10
# Number of threads used to call openWPM
NUMBER_OF_THREADS = 10

OPENWPM_FAIL_INCREASE = 1

LOCALHOST_URL = "localhost:5000"


# Django Mail
SERVER_EMAIL = "admin@newsletterme.de"
# ADMINS = [{{ lookup('passwordstore', 'privacymail/admin/contacts' )}}]
ADMINS = []
REMINDER_MAIL_THRESHOLD_IN_HOURS = 24


DISABLE_ADMIN_MAILS = False
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = "mail.newsletterme.de"
EMAIL_PORT = 587
# EMAIL_HOST_USER = '{{ lookup('passwordstore', 'privacymail/admin/send-user' )}}'
# EMAIL_HOST_PASSWORD = '{{ lookup('passwordstore', 'privacymail/admin/send-pass' )}}'
EMAIL_SUBJECT_PREFIX = "[PMail] "
# For debugging you may use the console backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Profiling
SILKY_PYTHON_PROFILER = True
# Authentication
SILKY_AUTHENTICATION = True  # User must login
SILKY_AUTHORISATION = True  # User must have permissions


sentry_sdk.init(
    dsn=os.getenv("RAVEN_DSN"),
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    # By default the SDK will try to use the SENTRY_RELEASE
    # environment variable, or infer a git commit
    # SHA as release, however you may want to set
    # something more human-readable.
    # release="myapp@1.0.0",
)

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "verbose": {
#             "format": (
#                 "%(levelname)s %(asctime)s %(module)s %(process)d "
#                 "%(thread)d %(message)s"
#             )
#         },
#         "console": {
#             "format": "[%(asctime)s][%(levelname)s] " "%(message)s",
#             "datefmt": "%H:%M:%S",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "INFO",
#             "class": "logging.StreamHandler",
#             "formatter": "console",
#         },
#     },
#     "loggers": {
#         "OpenWPM.automation.MPLogger": {
#             "level": "ERROR",
#             "handlers": ["console"],
#             "propagate": False,
#         },
#     },
# }
