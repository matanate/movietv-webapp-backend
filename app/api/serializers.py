from rest_framework import serializers
from app.models import Title, Review, Genre
from django.contrib.auth import get_user_model


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username
        token["is_staff"] = user.is_staff

        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "genre_name"]


class ReviewsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "comment",
            "date_posted",
        ]


class UpdateReviewsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "comment",
            "date_posted",
        ]
        read_only_fields = [
            "id",
            "title",
            "author",
        ]


class TitlesSerializer(serializers.ModelSerializer):
    # Use serializers.DateField with the format parameter
    release_date = serializers.DateField(format="%d/%m/%Y")

    reviews = ReviewsSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = "__all__"

    def to_internal_value(self, data):
        # Call the parent to_internal_value method
        internal_value = super().to_internal_value(data)

        # If genres field is present and it's a list of IDs, keep it as is
        if "genres" in data and isinstance(data["genres"], list):
            internal_value["genres"] = data["genres"]
        else:
            # If genres field is not present or not a list, set it to an empty list
            internal_value["genres"] = []

        return internal_value

    def create(self, validated_data):
        # in the validated data dictionary
        if "id" in self.initial_data:
            validated_data["id"] = self.initial_data["id"]

        # Pop genres data from validated_data to avoid direct assignment
        genres_data = validated_data.pop("genres", [])

        # Create the title instance without assigning genres
        title_instance = super().create(validated_data)

        # Add genres to the title using the set() method
        title_instance.genres.set(genres_data)

        return title_instance

    def to_representation(self, instance):
        # Call the parent to_representation method
        representation = super().to_representation(instance)

        # Replace the genres field with a list of genre names
        representation["genres"] = {
            genre.id: genre.genre_name for genre in instance.genres.all()
        }

        # Add list of reviews to the serializer
        representation["reviews"] = [
            {
                "id": review.id,
                "author_id": review.author.id,
                "author_username": review.author.username,
                "rating": review.rating,
                "comment": review.comment,
                "date_posted": review.date_posted.strftime("%B %d, %Y at %I:%M%p"),
            }
            for review in instance.reviews.all()
        ]
        return representation
