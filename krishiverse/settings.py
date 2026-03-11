from pathlib import Path
from django.utils.translation import gettext_lazy as _
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security settings ──────────────────────────────────────────────────────
# Use DJANGO_SECRET_KEY env var in production; fall back to dev key locally.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "krishiverse-ai-secret-key-2024-smart-farming-intelligence-platform"
)

DEBUG = False

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",         # serve static files (must be 2nd)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",          # i18n: language from URL/session/cookie
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "krishiverse.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "krishiverse.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

# ── Internationalisation ───────────────────────────────────────────────────
LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", _("English")),
    ("hi", _("Hindi")),
    ("pa", _("Punjabi")),
    ("ta", _("Tamil")),
    ("te", _("Telugu")),
    ("kn", _("Kannada")),
    ("bn", _("Bengali")),
    ("mr", _("Marathi")),
    ("ml", _("Malayalam")),
    # Note: "gu" (Gujarati) is not in Django 4.2's built-in language registry.
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

USE_I18N = True
USE_L10N = True
USE_TZ = True

TIME_ZONE = "Asia/Kolkata"

# ── Static files ───────────────────────────────────────────────────────────
STATIC_URL = "/static/"

# Only include the custom static/ dir if it actually exists (avoids
# collectstatic errors on a fresh clone that has no custom static assets).
_custom_static = BASE_DIR / "static"
STATICFILES_DIRS = [_custom_static] if _custom_static.is_dir() else []

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# WhiteNoise: compress + add cache-busting hashes to static files.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Session backend ─────────────────────────────────────────────────────────
# Use signed-cookie sessions so no DB writes are needed at runtime.
# This is important for Vercel serverless where the SQLite file is read-only.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# ── CSRF trusted origins (required when DEBUG=False) ───────────────────────
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://*.vercel.app,https://*.onrender.com,http://localhost:8000,http://127.0.0.1:8000"
).split(",")

# ── HTTPS / cookie security (Vercel terminates TLS at the edge) ────────────
# Tell Django about the HTTPS proxy header so it knows requests are secure.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Mark session/CSRF cookies as secure-only in production.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_DIR = BASE_DIR
