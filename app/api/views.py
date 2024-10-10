import os
import uuid

import requests
from app.models import Genre, Review, Title, ValidationToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django_filters.rest_framework import DjangoFilterBackend
from google.auth.transport import requests as g_requests
from google.oauth2 import id_token
from rest_framework import status, viewsets
from rest_framework.decorators import (action, api_view,
                                       authentication_classes,
                                       permission_classes)
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .filters import CustomOrdering, GenreFilter, ReviewFilter, TitleFilter
from .pagination import CustomPagination
from .premissions import IsCurrentUser
from .serializers import (ConfirmValidationSerializer, GenreSerializer,
                          PasswordResetSerializer, ReviewsSerializer,
                          TitlesSerializer, UserSerializer,
                          ValidationSerializer)

# TMDB API key
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
API_HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_API_KEY}",
}

# TMDB API URLs
URL_MOVIE_GENRES = "https://api.themoviedb.org/3/genre/movie/list?language=en"
URL_TV_GENRES = "https://api.themoviedb.org/3/genre/tv/list?language=en"

# Set the User model
User = get_user_model()



@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
def get_tmdb_search(request):
    """
    Fetches movie and TV genres from TMDB API and performs a search based on the provided search term.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        Response: The HTTP response object containing the search results.
    Raises:
        requests.RequestException: If there is an error fetching genres from TMDB API.
        Exception: If there is an error handling the search request.
    """
    # Fetching movie and TV genres from TMDB API
    try:
        movie_genres = requests.get(URL_MOVIE_GENRES, headers=API_HEADERS).json()[
            "genres"
        ]
        tv_genres = requests.get(URL_TV_GENRES, headers=API_HEADERS).json()["genres"]

        # Populate or create Genre instances
        for genre in movie_genres + tv_genres:
            Genre.objects.update_or_create(
                id=genre["id"], defaults={"genre_name": genre["name"]}
            )
    except requests.RequestException as e:
        print(f"Error fetching genres from TMDB API: {e}")
    
    # Performing search based on the provided search term and movie or TV
    try:
        search_term = request.GET.get("search_term", None)
        movie_or_tv = request.GET.get("movie_or_tv", "movie")
        # Check if search term is provided
        if search_term is None:
            return Response(
                {"error": "No search term provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        # Check if movie or tv is provided
        elif movie_or_tv is None:
            return Response(
                {"error": "No movie or tv provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Perform search
            url = f"https://api.themoviedb.org/3/search/{movie_or_tv}?query={search_term}&include_adult=false&language=en-US&page=1"
            response = requests.get(url, headers=API_HEADERS)
            response.raise_for_status()
            return Response(response.json()["results"], status=status.HTTP_200_OK)
    except Exception as e:
        # Handle exceptions
        return Response(
            {"error": f"{"\n".join(e.args)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

class BaseViewSet(viewsets.ModelViewSet):
    """
    Base viewset class that provides common functionality for all viewsets.
    Attributes:
        pagination_class (class): The pagination class to be used for paginated responses.
        filter_backends (list): The list of filter backends to be used for filtering the queryset.
        ordering_fields (str): The fields that can be used for ordering the queryset.
        authentication_classes (list): The list of authentication classes to be used for authentication.
    Methods:
        handle_exception(self, exc): Handles exceptions raised during the viewset's execution.
        list(self, request): Retrieves a list of objects from the queryset and returns a paginated response.
    """
    # Set base attributes
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, CustomOrdering]
    ordering_fields = "__all__"
    authentication_classes = [JWTAuthentication]  # Set JWT authentication globally


    def list(self, request):
        """
        Retrieve a list of objects.
        Args:
            request: The HTTP request object.
        Returns:
            If the `page_size` query parameter is set to "all", returns a response containing all objects.
            Otherwise, returns a paginated response containing a subset of objects.
        Raises:
            ValueError: If an error occurs during the retrieval process.
        """
        try:

            queryset = self.filter_queryset(self.get_queryset())  # Apply ordering
            # Check if the page_size query parameter is set to "all"
            if request.query_params.get("page_size") == "all":
                serializer = self.get_serializer(queryset, many=True)
                return Response({"count": queryset.count(), "results": serializer.data})

            # Paginate the queryset
            page = self.paginate_queryset(queryset)
            # Check if the page is not None and return the paginated response
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        # Handle exceptions
        except ValueError as e:
            return Response({"error": f"{"\n".join(e.args)}"}, status=status.HTTP_400_BAD_REQUEST)


# ViewSets for CRUD Operations
class TitleViewSet(BaseViewSet):
    """
    ViewSet for managing titles.
    Attributes:
        queryset (QuerySet): The queryset of Title objects.
        serializer_class (Serializer): The serializer class for Title objects.
        filterset_class (FilterSet): The filterset class for Title objects.
        ordering (list): The default ordering for Title objects.
    Methods:
        create(request, *args, **kwargs): Create a new Title object.
        get_permissions(): Get the permissions for the viewset.
    """
    # Set attributes
    queryset = Title.objects.all()
    serializer_class = TitlesSerializer
    filterset_class = TitleFilter
    # set default ordering
    ordering = ["-rating"]

    def create(self, request, *args, **kwargs):
        """
        Create a new object.
        Parameters:
        - request: The HTTP request object.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        Returns:
        - If the creation is successful, returns the created object.
        - If the title already exists, returns a response with an error message and status code 400.
        - If any other exception occurs, returns a response with the error message and status code 400.
        """
        # Handle exceptions
        try:
            response = super().create(request, *args, **kwargs)
            return response
        
        except IntegrityError as e:
            return Response({"error": "Title already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        except AuthenticationFailed as e:
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error during create: {str(e)}")
            return Response({"error": f"{"\n".join(e.args)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_permissions(self):
        """
        Returns a list of permission classes based on the action.

        If the action is 'list' or 'retrieve', the method returns [AllowAny] permission class.
        For other actions, it returns [IsAdminUser] permission class.

        Returns:
            list: A list of permission classes.
        """
        if self.action in [
            "list",
            "retrieve",
        ]:  # GET actions correspond to 'list' and 'retrieve'
            permission_classes = [AllowAny]
        else:
            permission_classes = [
                IsAdminUser
            ]  # Default to Admin users for other actions
        return [permission() for permission in permission_classes]
 
class ReviewViewSet(BaseViewSet):
    """
    A viewset for managing reviews.
    Attributes:
        queryset (QuerySet): The queryset of all reviews.
        serializer_class (Serializer): The serializer class for reviews.
        filterset_class (FilterSet): The filterset class for reviews.
        ordering (list): The default ordering for reviews.
    Methods:
        get_permissions: Get the permissions for different actions.
        perform_create: Perform additional actions after creating a review.
        perform_update: Perform additional actions after updating a review.
        create: Create a new review.
        partial_update: Partially update a review.
    """
    # Set attributes
    queryset = Review.objects.all()
    serializer_class = ReviewsSerializer
    filterset_class = ReviewFilter
    # set default ordering
    ordering = ["-date_posted"]

    def get_permissions(self):
        """
        Returns a list of permission classes based on the action being performed.

        - For the 'create' action (POST), the permission class is IsAuthenticated.
        - For the 'list' and 'retrieve' actions (GET), the permission class is AllowAny.
        - For the 'update' and 'partial_update' actions (PUT/PATCH), the permission class is IsCurrentUser.
        - For the 'destroy' action (DELETE), the permission classes are IsCurrentUser and IsAdminUser.
        - For other actions, the default permission class is IsAuthenticated.

        Returns:
            list: A list of permission classes.
        """
        if self.action in ["create"]:  # POST action corresponds to 'create'
            permission_classes = [IsAuthenticated]
        elif self.action in [
            "list",
            "retrieve",
        ]:  # GET actions correspond to 'list' and 'retrieve'
            permission_classes = [AllowAny]
        elif self.action in [
            "update",
            "partial_update",
        ]:  # PUT/PATCH actions
            permission_classes = [IsCurrentUser]
        elif self.action in [
            "destroy",
        ]:  # DELETE action
            permission_classes = [IsAdminUser | IsCurrentUser]
        else:
            permission_classes = [
                IsAuthenticated
            ]  # Default to authenticated users for other actions
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Perform additional actions when creating a new object.
        Args:
            serializer: The serializer instance used for object creation.
        Raises:
            ValidationError: If the user has already reviewed the title.
        Returns:
            None
        """
        # Check if the user has already reviewed the title and raise an error if they have
        if Review.objects.filter(
            author=self.request.user, title=serializer.validated_data["title"]
        ).exists():
            raise ValidationError(
                "You have already reviewed this title. You can only review each title once."
            )
        serializer.save(author=self.request.user, date_posted=timezone.now())

    def perform_update(self, serializer):
        """
        Updates an existing object instance.

        Args:
            serializer: The serializer instance used to validate and update the object.

        Returns:
            None
        """
        # Set the date_posted to the current datetime
        serializer.save(date_posted=timezone.now())

    # print error on create
    def create(self, request, *args, **kwargs):
        """
        Create a new object.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The HTTP response object.

        Raises:
            Exception: If an error occurs during the creation process.
        """
        # Handle exceptions
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": f"{"\n".join(e.args)}"}, status=status.HTTP_400_BAD_REQUEST)

    # on patch set date_posted to current datetime
    def partial_update(self, request, *args, **kwargs):
        """
        Partially updates a resource instance.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The HTTP response object.

        Raises:
            Exception: If an error occurs during the update.

        """
        # Handle exceptions
        try:
            request.data["date_posted"] = timezone.now()
            return super().partial_update(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": f"{"\n".join(e.args)}"}, status=status.HTTP_400_BAD_REQUEST)


class GenreViewSet(BaseViewSet):
    """
    A viewset for handling Genre objects.
    Inherits from BaseViewSet.
    Attributes:
        queryset (QuerySet): The queryset of Genre objects.
        serializer_class (Serializer): The serializer class for Genre objects.
        filterset_class (FilterSet): The filterset class for Genre objects.
    Methods:
        get_permissions: Returns the list of permissions for the viewset based on the action.
    """
    # Set attributes
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filterset_class = GenreFilter
    # set default ordering
    ordering = ["-id"]

    def get_permissions(self):
        """
        Returns a list of permission classes based on the action.

        If the action is 'list' or 'retrieve', the method returns [AllowAny] permission class.
        Otherwise, it returns [IsAdminUser] permission class.

        Returns:
            list: A list of permission classes.
        """
        if self.action in [
            "list",
            "retrieve",
        ]:  # GET actions correspond to 'list' and 'retrieve'
            permission_classes = [AllowAny]
        else:
            permission_classes = [
                IsAdminUser
            ]  # Default to Admin users for other actions
        return [permission() for permission in permission_classes]


class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for handling user-related operations.
    Methods:
    - create: Create a new user.
    - get_permissions: Get the permissions for the current action.
    Attributes:
    - queryset: The queryset of User objects.
    - serializer_class: The serializer class for User objects.
    - validation_serializer_class: The serializer class for validation.
    Raises:
    - Exception: If an error occurs during the create operation.
    Returns:
    - Response: The response object containing the created user or an error message.
    """
    # Set attributes
    queryset = User.objects.all()
    serializer_class = UserSerializer
    validation_serializer_class = ConfirmValidationSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new object.
        Args:
            request (HttpRequest): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            Response: The HTTP response object.
        Raises:
            Exception: If an error occurs during the creation process.
        """
        # Get the token and email from the request data
        token = request.data.pop("token")
        email = request.data.get("email")
        validation_serializer = self.validation_serializer_class(
            data={"token": token, "email": email}
        )
        # Validate the token
        try:
            validation_serializer.is_valid(raise_exception=True)
            # Hash the password before creating the user
            request.data["password"] = make_password(request.data["password"])

            #  delete or invalidate the token after use
            token_entry = ValidationToken.objects.get(token=token)
            token_entry.delete()
        
            return super().create(request, *args, **kwargs)
        # Handle exceptions
        except Exception as e:
            print(f"Error during create: {str(e)}")
            return Response({"error": f"{"\n".join(e.args)}"}, status=status.HTTP_400_BAD_REQUEST)

    
    def get_permissions(self):
        """
        Returns a list of permission classes based on the action being performed.

        - For "update" and "partial_update" actions, returns [IsCurrentUser] permission class.
        - For "retrieve" and "destroy" actions, returns [IsAdminUser | IsCurrentUser] permission class.
        - For "create" action, returns [AllowAny] permission class.
        - For all other actions, returns [IsAdminUser] permission class.

        Returns:
            list: A list of permission classes based on the action being performed.
        """
        if self.action in [
            "update",
            "partial_update",
        ]: # PUT/PATCH actions should be performed by the current user
            permission_classes = [IsCurrentUser] 
        elif self.action in ["retrieve", "destroy"]: # GET/DELETE actions should be performed by the current user or admin
            permission_classes = [IsAdminUser | IsCurrentUser]
        elif self.action in ["create"]: # POST action should be allowed for any user
            permission_classes = [AllowAny]
        else: # Default to Admin users for other actions
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ValidationViewSet(viewsets.ViewSet):
    """
    A viewset for handling email validation.
    Methods:
    - create(request): Create a validation token and send an email for email validation.
    Attributes:
    - serializer_class: The serializer class used for validation.
    """
    serializer_class = ValidationSerializer

    def create(self, request):
        """
        Create a new validation token and send a validation email.
        Parameters:
        - request: The HTTP request object.
        Returns:
        - Response: The HTTP response object.
        Raises:
        - ValidationError: If the serializer data is invalid.
        - Exception: If there is an error during email sending.
        """
        # Validate the serializer data
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Generate a reset token
        token = uuid.uuid4().hex

        # Save token and email mapping
        ValidationToken.objects.create(email=email, token=token)

        # Send the email
        subject = "AtMDB - Email validation"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = email
        html_message = render_to_string("mail_template.html", {"token": token})
        plain_message = strip_tags(html_message)
        try:
            send_mail(
                subject, plain_message, from_email, [to], html_message=html_message
            )

            return Response(
                {"detail": "Validation email has been sent."},
                status=status.HTTP_200_OK,
            )
        # Handle exceptions
        except Exception as e:
            print(f"Error during send email: {str(e)}")
            return Response(
               {"error": f"{"\n".join(e.args)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetViewSet(viewsets.ViewSet):
    """
    A viewset for resetting user passwords.
    Methods:
    - create: Resets the user password based on the provided token and email.
    Attributes:
    - serializer_class: The serializer class for password reset requests.
    - validation_serializer_class: The serializer class for validation requests.
    Raises:
    - Exception: If an error occurs during the password reset process.
    Returns:
    - Response: A response indicating the success or failure of the password reset operation.
    """

    serializer_class = PasswordResetSerializer
    validation_serializer_class = ConfirmValidationSerializer

    def create(self, request):
        """
        Create a new password for the user.
        Args:
            request (Request): The HTTP request object.
        Returns:
            Response: The HTTP response object.
        Raises:
            Exception: If an error occurs during the password reset process.
        """
        # Get the token and email from the request data
        token = request.data.get("token")
        email = request.data.get("email")

        # Set the validation serializer data
        validation_serializer = self.validation_serializer_class(
            data={type: "reset_password", "token": token, "email": email}
        )
        try:
            # Validate the token
            validation_serializer.is_valid(raise_exception=True)

            # Validate the password reset request
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Retrieve the token and new password
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            # Retrieve user and update the password
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            #  delete or invalidate the token after use
            token_entry = ValidationToken.objects.get(token=token)
            token_entry.delete()

            return Response(
                {"detail": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        # Handle exceptions
        except ValidationError as e:
            error_strings = "\n".join(
            error for key, error_list in e.detail.items() for error in error_list
            )

            return Response(
                {"error": error_strings},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValidationToken.DoesNotExist as e:
            return Response(
               {"error": f"{"\n".join(e.args)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for handling authentication related operations.
    Methods:
    - google_login: Handles Google login authentication.
    Attributes:
    - None
    """
    @action(detail=False, methods=["post"], url_path="google")
    def google_login(self, request):
        """
        Authenticates a user using Google login credentials.
        Parameters:
            request (Request): The HTTP request object.
        Returns:
            Response: The HTTP response containing the authentication tokens.
        Raises:
            ValueError: If the token is invalid.
        """
        credential = request.data.get("credential")
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                credential, g_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            # Check if the email is present in the token if not return an error
            if "email" not in idinfo:
                return Response(
                    {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create the user based on the email 
            email = idinfo["email"]
            first_name = idinfo.get("given_name", "")
            last_name = idinfo.get("family_name", "")
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            # Generate the access and refresh tokens
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )
        # Handle exceptions
        except ValueError as e:
            return Response(
                {"error": f"{"\n".join(e.args)}"}, status=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain pair view.
    
    Methods:
    - post: Overrides the default token obtain pair view to handle failed login attempts.
    - handle_exception: Handles exceptions raised during the token obtain process.
    """

    def post(self, request, *args, **kwargs):
        """
        Overrides the default token obtain pair view to handle failed login attempts.

        This method overrides the default token obtain pair view to check if the account is locked
        before proceeding with the normal token obtain process. If the account is locked, it raises
        an AuthenticationFailed exception. If the account is not locked, it resets the failed
        attempts if the token obtain is successful.

        Parameters:
        - request: The HTTP request object.
        - *args: Variable length argument list.
        - **kwargs: Arbitrary keyword arguments.

        Returns:
        - Response: The HTTP response object containing the access and refresh tokens.

        Raises:
        - AuthenticationFailed: If the account is locked due to multiple failed login attempts.
        """
        user = User.objects.filter(email=request.data.get('email')).first()

        if user:
            # Check if the account is locked
            if user.is_locked and user.lock_until and user.lock_until > timezone.now():
                raise AuthenticationFailed("Your account has been locked due to multiple failed login attempts.")

            # Proceed with the normal token obtain process
            response = super().post(request, *args, **kwargs)
            
            # If successful, reset failed attempts
            user.reset_failed_attempts()
            return response
        
        return super().post(request, *args, **kwargs)

    def handle_exception(self, exc):
        """
        Handles exceptions raised during the token obtain process.

        If the exception is an InvalidToken exception, it checks if the account is locked
        due to multiple failed login attempts. If the account is not locked, it increments
        the failed attempts if the login failed. If the failed attempts reach the maximum
        allowed, it locks the account. It appends a message to the error string indicating 
        the remaining attempts or if the account is locked.

        Parameters:
        - exc: The exception object.

        Returns:
        - Response: The HTTP response object containing the error message.
        """
        if isinstance(exc, AuthenticationFailed):
            email = self.request.data.get('email')
            user = User.objects.filter(email=email).first()

            if user:
                # Increment failed attempts if login failed
                user.failed_login_attempts += 1
                remaining_attempts = settings.MAX_FAILED_LOGIN_ATTEMPTS - user.failed_login_attempts
                if remaining_attempts == 0:
                    user.lock_account()
                if user.is_locked:
                    exc.detail = "Your account has been locked due to multiple failed login attempts."

                user.save()                

        return super().handle_exception(exc)
