import os

from .settings import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME"),
        "USER": os.environ.get("DATABASE_USER"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
        "HOST": "db",  # Name of the PostgreSQL service in docker-compose.yml
        "PORT": 5432,  # Default port for PostgreSQL
    }
}

FORCE_SCRIPT_NAME = "/backend"
