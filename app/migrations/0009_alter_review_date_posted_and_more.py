# Generated by Django 5.0.3 on 2024-03-10 08:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0008_rename_ratings_title_rating_alter_review_author"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="review", name="date_posted", field=models.DateTimeField(),
        ),
        migrations.AlterUniqueTogether(
            name="review", unique_together={("author", "title")},
        ),
    ]
