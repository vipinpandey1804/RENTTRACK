"""
Local development settings — runs without Docker using SQLite.

Use when you don't have PostgreSQL/Redis available:
  DJANGO_SETTINGS_MODULE=config.settings.local python manage.py runserver
"""
from .dev import *  # noqa: F401, F403

# SQLite — no Postgres needed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# In-memory cache — no Redis needed
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Run Django Q tasks synchronously — no worker process needed
Q_CLUSTER = {"sync": True, "orm": "default"}

# Print emails to console instead of sending via SMTP
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
