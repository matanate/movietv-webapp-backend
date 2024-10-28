from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

# Create a router object
router = DefaultRouter()

# Register viewsets with the router
router.register(r"titles", views.TitleViewSet, basename="title")
router.register(r"reviews", views.ReviewViewSet, basename="review")
router.register(r"genres", views.GenreViewSet, basename="genre")
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"validation", views.ValidationViewSet, basename="validation")
router.register(
    r"password-reset",
    views.PasswordResetViewSet,
    basename="password_reset",
)
router.register(r"auth", views.AuthViewSet, basename="auth")

# Define the URL patterns
urlpatterns = [
    # Authentication
    path(
        "token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),  # Obtain JWT token
    path(
        "token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),  # Refresh JWT token
    # Application
    path("", include(router.urls)),  # Include router URLs
    path(
        "get-tmdb-search/", views.get_tmdb_search, name="get_tmdb_search"
    ),  # Custom search endpoint
]
