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

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
