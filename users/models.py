from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=100, unique=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    lock_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def lock_account(self):
        self.is_locked = True
        self.lock_until = timezone.now() + timedelta(minutes=30)  # Lock for 30 minutes
        self.save()

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.is_locked = False
        self.lock_until = None
        self.save()
