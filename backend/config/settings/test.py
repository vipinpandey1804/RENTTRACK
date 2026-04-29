"""Test settings — fast, isolated, in-memory where possible."""

from .base import *  # noqa: F401, F403

DEBUG = False

# Use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Don't hit Redis in tests
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Run Django Q tasks synchronously in tests
Q_CLUSTER = {"sync": True, "orm": "default"}

# Fast password hashing
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Email sent to memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
