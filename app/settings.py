# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from signalbox.configurable_settings import *
from signalbox.utilities.get_env_variable import get_env_variable
import twilio
from twilio.rest import TwilioRestClient
import imp
import sys
import os
import socket
import string

sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))


# This must be set but using random string#
SECRET_KEY = get_env_variable('SECRET_KEY',
    required=True,
    default=shortuuid.uuid(),
    warning="USING RANDOM SECRET KEY - SESSIONS MAY NOT PERSIST")


try:
    TESTING = 'test' == sys.argv[1]
except IndexError:
    TESTING = False


# yaml setting - can be set as "true" or "false" but not "True"/"False"
DEBUG = bool(get_env_variable('DEBUG', required=False, default=False, as_yaml=True))


# Display and admin functionality
USE_I18N = False
USE_L10N = False
LANGUAGE_CODE = get_env_variable('LANGUAGE_CODE', default='en')
TIME_ZONE = get_env_variable('TIME_ZONE', default='Europe/London')


# the name of the site which appears in the header
BRAND_NAME = get_env_variable('BRAND_NAME', default="SignalBox")


# BACKEND
os.environ["REUSE_DB"] = "1" # a sensible default
DB_URL = get_env_variable('DATABASE_URL', required=False, default="postgres://localhost/sbox")
DATABASES = {'default': dj_database_url.config(default=DB_URL)}



# DON'T LEAVE ME THIS WAY!!!!
SECRET_KEY = get_env_variable('SECRET_KEY', default="boohoohoo")
DEBUG = get_env_variable('DEBUG', default=True)


from signalbox.configurable_settings import *
from signalbox.settings import *

# amazon files settings
AWS_ACCESS_KEY_ID = get_env_variable('AWS_ACCESS_KEY_ID', default="")
AWS_SECRET_ACCESS_KEY = get_env_variable('AWS_SECRET_ACCESS_KEY', default="")
AWS_STORAGE_BUCKET_NAME = get_env_variable("AWS_STORAGE_BUCKET_NAME", default="",)
AWS_QUERYSTRING_AUTH = get_env_variable('AWS_QUERYSTRING_AUTH', default=False)


##### OVERRIDING EMAIL SETTINGS #####

EMAIL_USE_TLS = True
EMAIL_HOST = get_env_variable('MAILGUN_SMTP_SERVER', required=False)
EMAIL_PORT = int(get_env_variable('MAILGUN_SMTP_PORT', required=False, default="587"))
EMAIL_HOST_USER = get_env_variable('MAILGUN_SMTP_LOGIN', required=False)
EMAIL_HOST_PASSWORD = get_env_variable('MAILGUN_SMTP_PASSWORD', required=False, )



HERE = os.path.realpath(os.path.dirname(__file__))
PROJECT_PATH, SETTINGS_DIR = os.path.split(HERE)
DJANGO_PATH, APP_NAME = os.path.split(PROJECT_PATH)

#####  FILEs  #####
USER_UPLOAD_STORAGE_BACKEND = 'signalbox.s3.PrivateRootS3BotoStorage'
# MAIN_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# DEFAULT_FILE_STORAGE = 'signalbox.s3.MediaRootS3BotoStorage'


STATIC_ROOT = os.path.join(PROJECT_PATH, 'staticfiles')
STATIC_URL = '/static/'


TEMPLATE_STRING_IF_INVALID = ""


##### STANDARD DJANGO STUFF #####
ROOT_URLCONF = 'urls'
SITE_ID = 1
SESSION_ENGINE = "django.contrib.sessions.backends.file"

LOG_DATABASE_QUERIES = get_env_variable('LOG_DATABASE_QUERIES', default=False)


MIDDLEWARE_CLASSES = (
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    USE_VERSIONING and 'reversion.middleware.RevisionMiddleware' or None,
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'signalbox.middleware.filter_persist_middleware.FilterPersistMiddleware',
    'signalbox.middleware.loginformmiddleware.LoginFormMiddleware',
    'signalbox.middleware.adminmenumiddleware.AdminMenuMiddleware',
    'signalbox.middleware.error_messages_middleware.ErrorMessagesMiddleware',
    'twiliobox.middleware.speak_error_messages_middleware.SpeakErrorMessagesMiddleware',
    "djangosecure.middleware.SecurityMiddleware",
    'django.middleware.locale.LocaleMiddleware',
)

ATOMIC_REQUESTS = True

MIDDLEWARE_CLASSES = list(filter(bool, MIDDLEWARE_CLASSES))

_TEMPLATE_LOADERS = (
    'apptemplates.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS':{
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'signalbox.context_processors.globals',
                'sekizai.context_processors.sekizai'
            ),
            # 'loaders': (
            #     ('django.template.loaders.cached.Loader', _TEMPLATE_LOADERS),
            # )
            'loaders': _TEMPLATE_LOADERS,
        },
    },
]


# caching enabled because floppyforms is slow otherwise; disable for development



INSTALLED_APPS = [
    'frontend',
    'ask',
    'twiliobox',
    'djangosecure',
    'signalbox',
    'django.contrib.auth',
    'django.contrib.redirects',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'registration',
    USE_VERSIONING and 'reversion' or None,
    'django_extensions',
    'menus',
    'sekizai',
    'selectable',
    'storages',
    'floppyforms',
    'bootstrap_pagination',
    'rest_framework',
    'debug_toolbar',
    'mathfilters',
    'cachalot',
    'phonenumber_field',
]

# filter out conditionally-skipped apps (which create None's)
INSTALLED_APPS = list(filter(bool, INSTALLED_APPS))

# REGISTRATION #
AUTH_PROFILE_MODULE = 'signalbox.UserProfile'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: "/accounts/profile/",
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'testlogger': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}



# Pre load some models when we use shell_plus for convenience in using the repl
SHELL_PLUS_PRE_IMPORTS = (
    ('signalbox.models', ('*',)),
    ('ask.models', '*'),
    ('django.contrib.auth.models', 'User'),
)


# security-related settings
# see https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
INTERNAL_IPS = ['127.0.0.1',]
ALLOWED_HOSTS = get_env_variable('ALLOWED_HOSTS', default="127.0.0.1;.herokuapp.com").split(";")
SESSION_COOKIE_HTTPONLY = get_env_variable('SESSION_COOKIE_HTTPONLY', default=True)
SECURE_FRAME_DENY = True
SECURE_BROWSER_XSS_FILTER = get_env_variable('SECURE_BROWSER_XSS_FILTER', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = get_env_variable('SECURE_CONTENT_TYPE_NOSNIFF', default=True)
SECURE_SSL_REDIRECT = get_env_variable('SECURE_SSL_REDIRECT', required=False, default=False)
SESSION_COOKIE_AGE = get_env_variable('SESSION_COOKIE_AGE', default=2 * 60 * 60)  # 2 hours in seconds
SESSION_SAVE_EVERY_REQUEST = get_env_variable('SESSION_SAVE_EVERY_REQUEST', default=True)
SESSION_EXPIRE_AT_BROWSER_CLOSE = get_env_variable('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True)

# disable secure cookies not a great idea?
SESSION_COOKIE_SECURE = get_env_variable('SESSION_COOKIE_SECURE', default=False)

# SECURITY BITS WHICH ARE NOT CUSTOMISABLE FROM ENV VARS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')



# DEBUG TOOLBAR SETUP
DEBUG_TOOLBAR_PATCH_SETTINGS = False

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel'
]


# CACHING

CACHALOT_ENABLED = get_env_variable('CACHALOT_ENABLED', default=True)

# this is just the default
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake2',
    }
}
