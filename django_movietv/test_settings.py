from .settings import *

DEBUG = True

# Use an in-memory database for speed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use console backend to avoid sending real emails
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable caching during tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
