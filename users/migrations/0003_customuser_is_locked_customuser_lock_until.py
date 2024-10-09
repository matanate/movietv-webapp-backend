# Generated by Django 5.0.3 on 2024-10-09 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_remove_customuser_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_locked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="lock_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
