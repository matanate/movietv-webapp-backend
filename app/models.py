from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

User = get_user_model()


def generate_unique_id():
    ids = Title.objects.all().values_list("id", flat=True)
    if not ids:
        return 1
    for i in range(1, max(ids) + 1):
        if i not in ids:
            return i
    return max(ids) + 1


# Titles model with relationship to Reviews
class Title(models.Model):
    id = models.IntegerField(
        primary_key=True, default=generate_unique_id, editable=False
    )
    title = models.CharField(max_length=200, unique=False, null=False)
    release_date = models.DateField(unique=False, null=False)
    overview = models.TextField(max_length=1000, unique=False, null=False)
    img_url = models.CharField(max_length=1000, unique=False, null=False)
    movie_or_tv = models.CharField(
        max_length=20,
        unique=False,
        null=False,
        choices=(("movie", "movie"), ("tv", "tv")),
    )
    rating = models.FloatField(
        unique=False, null=False, default=0.0
    )  # Average rating for the title

    genres = models.ManyToManyField("Genre", related_name="titles", blank=True)

    def __str__(self):
        return self.title

    def update_average_rating(self):
        # Calculate the average rating for the title
        total_ratings = sum(review.rating for review in self.reviews.all())
        num_reviews = self.reviews.count()
        avg_rating = total_ratings / num_reviews if num_reviews > 0 else 0.0
        self.rating = round(avg_rating, 1)
        self.save()


# Reviews model with relationships to Users and Titles
class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    rating = models.FloatField(unique=False, null=False, default=0.0)
    comment = models.TextField(max_length=200, unique=False, null=False)
    date_posted = models.DateTimeField(unique=False, null=False, auto_now_add=True)
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, null=False, related_name="reviews"
    )

    class Meta:
        # Enforce unique constraint on the combination of author and title
        unique_together = ["author", "title"]

    def __str__(self):
        return f"Review by {self.author.username} on {self.title.title}"


class Genre(models.Model):
    genre_name = models.CharField(max_length=200, unique=True, null=False)

    def __str__(self):
        return self.genre_name


class ValidationToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset token for user: {self.email}"


# Listen for the post_save event to update average ratings
@receiver(post_save, sender=Review)
def update_average_rating_on_review_save(sender, instance, **kwargs):
    if instance.title:
        # Update the average rating for the corresponding Title
        instance.title.update_average_rating()


# Listen for the post_delete event to update average ratings
@receiver(post_delete, sender=Review)
def update_average_rating_on_review_delete(sender, instance, **kwargs):
    if instance.title:
        # Update the average rating for the corresponding Title
        instance.title.update_average_rating()
