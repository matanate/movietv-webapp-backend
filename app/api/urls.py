from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Authentication
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("create-user/", views.create_user),
    # Application
    path("get-titles/", views.get_titles),
    path("get-titles/<int:title_id>", views.get_title),
    path("create-review/", views.create_review),
    path("edit-review/", views.edit_review),
    path("get-tmdb-search/", views.get_tmdb_search),
    path("add-title/", views.add_title),
    path("delete-title/<int:title_id>", views.delete_title),
    path("delete-review/<int:review_id>", views.delete_review),
]
