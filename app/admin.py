from django.contrib import admin

from .models import Genre, Review, Title, ValidationToken

admin.site.register(Title)
admin.site.register(Review)
admin.site.register(Genre)
admin.site.register(ValidationToken)
