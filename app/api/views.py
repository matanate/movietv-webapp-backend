from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ValidationError
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from app.models import Title, Review, Genre
from .serializers import (
    UserSerializer,
    TitlesSerializer,
    ReviewsSerializer,
    UpdateReviewsSerializer,
)

from django.contrib.auth import get_user_model
import requests
import os
from math import ceil

# TMDB API key
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
API_HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_API_KEY}",
}


User = get_user_model()


@api_view(["POST"])
def create_user(request):
    serializer = UserSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)

        # Create the user and set the password using set_password
        user = User.objects.create(
            email=serializer.validated_data["email"],
            username=serializer.validated_data["username"],
        )
        user.set_password(serializer.validated_data["password"])
        user.save()
        return Response(
            {"message": "User registered successfully"}, status=status.HTTP_201_CREATED
        )
    except ValidationError as e:

        if "email" in e.detail:
            # Handle the case when the email already exists
            error_message = (
                f"User with email '{serializer.data['email']}' already exists."
            )
            return Response(
                {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        elif "username" in e.detail:
            # Handle the case when the username already exists
            error_message = (
                f"User with username '{serializer.data['username']}' already exists."
            )
            return Response(
                {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def get_titles(request):
    try:
        search_term = request.data.get("search_term", None)
        order_by = request.data.get("order_by", "rating")
        is_ascending = request.data.get("is_ascending", True)
        movie_or_tv = request.data.get("movie_or_tv", "all")
        title_per_page = request.data.get("title_per_page", 10)
        page_number = request.data.get("page_number", 1)

        # Query titles based on search term and movie_or_tv
        if search_term:
            if movie_or_tv == "all":
                titles_query = Title.objects.filter(title__icontains=search_term)
            else:
                titles_query = Title.objects.filter(
                    movie_or_tv=movie_or_tv, title__icontains=search_term
                )
        else:
            if movie_or_tv == "all":
                titles_query = Title.objects.all()
            else:
                titles_query = Title.objects.filter(movie_or_tv=movie_or_tv)

        # Calculate total number of titles and pages
        total_titles = titles_query.count()
        total_pages = ceil(total_titles / title_per_page)

        # Apply ordering, pagination, and serialization
        if is_ascending:
            order_by = "-" + order_by

        titles = titles_query.order_by(f"{order_by}")[
            (page_number - 1) * title_per_page : page_number * title_per_page
        ]

        serializer = TitlesSerializer(titles, many=True)

        return Response({"titles": serializer.data, "total_pages": total_pages})
    except Exception as e:  # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_title(request, title_id):
    try:
        serializer = TitlesSerializer(Title.objects.get(pk=title_id))
        return Response(serializer.data)
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_review(request):
    # Set the date_posted field to the current date and time
    request.data["date_posted"] = timezone.now()

    serializer = ReviewsSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Review added successfully"}, status=status.HTTP_201_CREATED
        )
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_review(request):
    review = Review.objects.get(pk=request.data.get("id"))
    # Set the date_posted field to the current date and time
    request.data["date_posted"] = timezone.now()
    if request.data.pop("author") != review.author.id:
        return Response(
            {"error": "You can only edit your own reviews"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = UpdateReviewsSerializer(instance=review, data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Review updated successfully"}, status=status.HTTP_202_ACCEPTED
        )
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
def get_tmdb_search(request):
    try:
        search_term = request.GET.get("search-term", None)
        movie_or_tv = request.GET.get("movie-or-tv", "movie")
        if search_term is None:
            return Response(
                {"error": "No search term provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        elif movie_or_tv is None:
            return Response(
                {"error": "No movie or tv provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            url = f"https://api.themoviedb.org/3/search/{movie_or_tv}?query={search_term}&include_adult=false&language=en-US&page=1"
            response = requests.get(url, headers=API_HEADERS)
            response.raise_for_status()
            return Response(response.json()["results"], status=status.HTTP_200_OK)
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
def add_title(request):
    serializer = TitlesSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Title added successfully"}, status=status.HTTP_201_CREATED
        )
    except IntegrityError as e:

        return Response(
            {"error": f"Title already exists: {e}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
def delete_title(request, title_id):
    try:
        title = Title.objects.get(pk=title_id)
        title.delete()
        return Response(
            {"message": "Title deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )
    # catch id not found errors
    except Title.DoesNotExist:
        return Response({"error": "Title not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
def delete_review(request, review_id):
    try:
        title = Review.objects.get(pk=review_id)
        title.delete()
        return Response(
            {"message": "Review deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
    # catch id not found errors
    except Title.DoesNotExist:
        return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Handle other exceptions
        return Response(
            {"error": f"An error occurred: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
