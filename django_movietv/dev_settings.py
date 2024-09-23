from .settings import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase.db.sqlite3",
    },
    "test": {
        "NAME": f"test_mydatabase.db.sqlite3",
    },
}
