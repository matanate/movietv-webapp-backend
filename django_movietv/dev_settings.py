from .settings import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase.db.sqlite3",
    },
}

# Use console backend to avoid sending real emails
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
