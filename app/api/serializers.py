from datetime import timedelta

from app.models import Genre, Review, Title, ValidationToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# Get the user model
User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token obtain pair serializer.
    This serializer extends the TokenObtainPairSerializer class and adds custom claims to the token.
    """

    @classmethod
    def get_token(cls, user):
        """
        Get the token with custom claims.
        """
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username
        token["is_staff"] = user.is_staff

        return token


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for the Genre model.
    """

    class Meta:
        model = Genre
        fields = ["id", "genre_name"]


class ReviewsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.
    """

    # Add the author's username to the serialized data
    author_name = serializers.ReadOnlyField(source="author.username")
    # Add the author's initials to the serialized data
    author_initials = serializers.SerializerMethodField(read_only=True)

    def get_author_initials(self, obj):
        """
        Return the author's initials.
        """
        return f"{obj.author.first_name[0].upper()}{obj.author.last_name[0].upper()}"

    class Meta:
        model = Review
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "comment",
            "date_posted",
            "author_name",
            "author_initials",
        ]
        read_only_fields = [
            "id",
            "author",
            "author_name",
            "author_initials",
            "date_posted",
        ]

    def update(self, instance, validated_data):
        # Remove the read-only field from the validated data if it's present
        validated_data.pop("field_to_protect", None)
        return super().update(instance, validated_data)


class TitlesSerializer(serializers.ModelSerializer):
    """
    Serializer for the Title model.
    """

    # Add the reviews to the serialized data
    release_date = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = Title
        fields = [
            "id",
            "release_date",
            "reviews",
            "title",
            "overview",
            "img_url",
            "movie_or_tv",
            "rating",
            "genres",
        ]
        read_only_fields = ["reviews"]

    def create(self, validated_data):
        # Add the ID to the validated data if it's present in the initial data
        if "id" in self.initial_data:
            validated_data["id"] = self.initial_data["id"]

        title_instance = super().create(validated_data)

        return title_instance


class ValidationSerializer(serializers.Serializer):
    """
    Serializer for validating user input data.
    """

    # Add the type field to the serializer
    type = serializers.ChoiceField(
        required=True,
        choices=[("register", "Register"), ("reset_password", "Reset password")],
    )
    # Add the email field to the serializer
    email = serializers.EmailField(required=True)

    def validate(self, data):
        email = data.get("email")
        type = data.get("type")
        # Validate the email and type fields
        if not email:
            raise serializers.ValidationError("No email provided.")
        if type == "register":
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("Email already exists.")
        elif type == "reset_password":
            if not User.objects.filter(email=email).exists():
                raise serializers.ValidationError("Email not found.")
        return data


class ConfirmValidationSerializer(serializers.Serializer):
    """
    Serializer for confirming validation.
    """

    # Add the email and token fields to the serializer
    email = serializers.EmailField()
    token = serializers.CharField()

    def validate(self, data):
        token = data.get("token")
        email = data.get("email")
        # Validate the email and token fields
        if not token:
            raise serializers.ValidationError("No token provided.")
        if not email:
            raise serializers.ValidationError("No email provided.")
        # Check if the token is valid
        token_entry = ValidationToken.objects.get(token=token)
        if (
            token_entry.email != email
            or not token_entry
            or token_entry.created_at < (timezone.now() - timedelta(minutes=3))
        ):
            raise serializers.ValidationError("Invalid or expired token.")
        return data


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for resetting user password.
    """

    # Add the email, new_password, and token fields to the serializer
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=8, max_length=128)
    token = serializers.CharField()

    def validate(self, data):
        new_password = data.get("new_password")
        token = data.get("token")
        email = data.get("email")
        # Validate the email, new_password, and token fields
        if not new_password:
            raise serializers.ValidationError("No password provided.")
        if not token:
            raise serializers.ValidationError("No token provided.")
        if not email:
            raise serializers.ValidationError("No email provided.")
        return data
