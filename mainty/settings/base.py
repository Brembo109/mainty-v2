import environ
from datetime import timedelta
from pathlib import Path

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.audit",
    "apps.assets",
    "apps.contracts",
    "apps.maintenance",
    "apps.qualification",
    "apps.tasks",
    "apps.notifications",
    "apps.calibration",
]

THIRD_PARTY_APPS = [
    "axes",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "apps.audit.middleware.AuditMiddleware",
    "apps.accounts.middleware.PasswordExpiryMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mainty.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.notifications.context_processors.notifications",
            ],
            "builtins": [
                "apps.core.templatetags.filter_tags",
            ],
        },
    },
]

WSGI_APPLICATION = "mainty.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://mainty:mainty@db:5432/mainty")
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalisation
LANGUAGE_CODE = "de"
LANGUAGES = [
    ("de", "Deutsch"),
    ("en", "English"),
]
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static" / "dist"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model — must be set before first migration
AUTH_USER_MODEL = "accounts.User"

# Authentication backends — AxesStandaloneBackend must be first
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Auth redirects
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:index"
LOGOUT_REDIRECT_URL = "accounts:login"

# Password rotation (days)
PASSWORD_EXPIRY_DAYS = env.int("PASSWORD_EXPIRY_DAYS", default=90)

# Contracts — days before expiry to show "läuft aus" warning
CONTRACT_EXPIRY_WARNING_DAYS = env.int("CONTRACT_EXPIRY_WARNING_DAYS", default=90)

# django-axes — brute-force protection
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["username"]]
AXES_LOCKOUT_CALLABLE = "apps.accounts.utils.axes_lockout_response"

# Session — lock down from day one
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

# Email defaults (overridden per environment)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="mainty@localhost")
EMAIL_BACKEND = env("EMAIL_BACKEND", default="apps.core.backends.SiteConfigEmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

# Reminder command
SITE_URL = env("SITE_URL", default="http://localhost:8000")
REMINDER_EMAIL_SUBJECT = env("REMINDER_EMAIL_SUBJECT", default="[mainty] GMP-Erinnerung — Handlungsbedarf")
