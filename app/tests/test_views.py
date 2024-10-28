import datetime
from datetime import timedelta
from unittest.mock import patch

from app.models import Genre, Review, Title, ValidationToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()


class BaseTestViewSet(APITestCase):
    """
    Base class for all viewset test cases. This class provides
    the setup for the test cases and some utility functions.

    The setup includes creating three users: adminuser, testuser, and otheruser,
    and generating refresh tokens and access tokens for them.

    The utility functions provided are:
    - create_title: Creates a title with two genres.
    - create_genre: Creates a genre.
    - create_review: Creates a review for a given title.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Setup the test data.

        This function is called once before all the test cases.
        """
        # Check if model_name is defined, raise an error if not
        if not hasattr(cls, "url_name"):
            raise AttributeError("Test case must define 'url_name'.")

        cls.list_url = reverse(f"{cls.url_name}-list")
        cls.detail_url = lambda *args, **kwargs: reverse(
            f"{cls.url_name}-detail", args=args, kwargs=kwargs
        )

        # Create the admin user
        cls.admin_user = User.objects.create_superuser(
            email="adminuser@example.com",
            password="adminpassword123",
            username="adminuser",
            is_staff=True,
        )
        # Create the test user
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            username="testuser",
        )
        # Create the other user
        cls.other_user = User.objects.create_user(
            email="otheruser@example.com",
            password="password123",
            username="otheruser",
        )
        # Generate a refresh token and an access token for the test user
        cls.refresh = RefreshToken.for_user(cls.user)
        cls.access_token = str(cls.refresh.access_token)
        # Generate a refresh token and an access token for the admin user
        cls.admin_refresh = RefreshToken.for_user(cls.admin_user)
        cls.admin_access_token = str(cls.admin_refresh.access_token)
        # Generate a refresh token and an access token for the other user
        cls.other_refresh = RefreshToken.for_user(cls.other_user)
        cls.other_access_token = str(cls.other_refresh.access_token)

    def setUp(self):
        """
        Setup the client.

        This function is called once before each test case.
        """
        self.client = APIClient()

    def create_title(
        self,
        title="Test Movie",
        movie_or_tv="movie",
        release_date=datetime.date(2022, 1, 1),
        overview="This is a test movie.",
        img_url="http://example.com/movie.jpg",
        genre_1="Genre 1",
        genre_2="Genre 2",
    ):
        """
        Creates a title with two genres.

        Returns:
            Title: The created title.
        """

        # Create the title
        title = Title.objects.create(
            title=title,
            release_date=release_date,
            overview=overview,
            img_url=img_url,
            movie_or_tv=movie_or_tv,
        )

        # Create or get two genres
        if genre_1:
            genre_1_obj, _ = Genre.objects.get_or_create(genre_name=genre_1)
            title.genres.add(genre_1_obj)
        if genre_2:
            genre_2_obj, _ = Genre.objects.get_or_create(genre_name=genre_2)
            title.genres.add(genre_2_obj)

        # Return the title
        return title

    def create_genre(self, genre_name):
        """
        Creates a genre.

        Args:
            genre_name (str): The name of the genre.

        Returns:
            Genre: The created genre.
        """
        return Genre.objects.create(genre_name=genre_name)

    def create_review(self, title, rating=4.5, comment="Great movie!"):
        """
        Creates a review for a given title.

        Args:
            title (Title): The title to create the review for.

        Returns:
            Review: The created review.
        """
        return Review.objects.create(
            author=self.user, rating=rating, comment=comment, title=title
        )


class TestTitleViewSet(BaseTestViewSet):
    """
    Test cases for the TitleViewSet.

    This class contains tests for various actions on the TitleViewSet, including:
    - Creating a title without authentication
    - Creating a title as a non-staff user
    - Creating a title as a staff user
    - Creating a duplicate title
    - Creating a title with invalid data
    - Updating a title without authentication
    - Updating a title as a non-staff user
    - Updating a title as a staff user
    - Deleting a title without authentication
    - Deleting a title as a non-staff user
    - Deleting a title as a staff user
    - Retrieving title details without authentication
    - Listing titles without authentication
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for the test case.

        This method is called once before all the test cases.
        """
        cls.url_name = "title"
        super().setUpTestData()
        cls.title = cls.create_title(cls)

    def test_title_viewset_create_without_token(self):
        """
        Test case for creating a title without authentication.

        This test case tests that a 401 status code is returned when
        a title is created without authentication.
        """
        self.client.credentials()  # Remove token
        data = {
            "title": "New Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is a new movie.",
            "imgUrl": "http://example.com/new_movie.jpg",
            "movieOrTv": "movie",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            "Authentication Credentials Were Not Provided.",
            response.data["error"],
        )

    def test_title_viewset_create_not_staff(self):
        """
        Test case for creating a title as a non-staff user.

        This test case tests that a 403 status code is returned when
        a title is created as a non-staff user.
        """
        data = {
            "title": "New Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is a new movie.",
            "imgUrl": "http://example.com/new_movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_title_viewset_create_staff(self):
        """
        Test case for creating a title as a staff user.

        This test case tests that a 201 status code is returned when
        a title is created as a staff user.
        """
        data = {
            "title": "New Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is a new movie.",
            "imgUrl": "http://example.com/new_movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_title = Title.objects.get(title="New Movie")
        self.assertEqual(new_title.title, "New Movie")
        self.assertEqual(new_title.release_date, datetime.date(2022, 1, 1))
        self.assertEqual(new_title.overview, "This is a new movie.")
        self.assertEqual(new_title.img_url, "http://example.com/new_movie.jpg")
        self.assertEqual(new_title.movie_or_tv, "movie")

    def test_title_viewset_create_duplicate(self):
        """Test case for creating a duplicate title.

        This test case tests that a 400 status code is returned when
        a duplicate title is created.
        """
        data = {
            "id": self.title.id,
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Title Already Exists.", response.data["error"])

    def test_title_viewset_create_without_title(self):
        """Test case for creating a title without a title.

        This test case tests that a 400 status code is returned when
        a title is created without a title.
        """
        data = {
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Title Is Required.", response.data["error"])

    def test_title_viewset_create_without_release_date(self):
        """Test case for creating a title without a release date.

        This test case tests that a 400 status code is returned when
        a title is created without a release date.
        """
        data = {
            "title": "Movie",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Release Date Is Required.", response.data["error"])

    def test_title_viewset_create_without_movie_or_tv(self):
        """Test case for creating a title without a movie or tv.

        This test case tests that a 400 status code is returned when
        a title is created without a movie or tv.
        """
        data = {
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Movie Or Tv Is Required.", response.data["error"])

    def test_title_viewset_create_without_overview(self):
        """Test case for creating a title without an overview.

        This test case tests that a 400 status code is returned when
        a title is created without an overview.
        """
        data = {
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Overview Is Required.", response.data["error"])

    def test_title_viewset_create_without_img_url(self):
        """Test case for creating a title without an image URL.

        This test case tests that a 400 status code is returned when
        a title is created without an image URL.
        """
        data = {
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Img Url Is Required.", response.data["error"])

    def test_title_viewset_create_invalid_date(self):
        """Test case for creating a title with invalid data.

        This test case tests that a 400 status code is returned when
        an invalid releaseDate value is provided.
        """
        data = {
            "title": "Movie",
            "releaseDate": "invalid_date",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "Date Has Wrong Format. Use One Of These Formats Instead: Yyyy-Mm-Dd.",
            response.data["error"],
        )

    def test_title_viewset_create_invalid_movie_or_tv(self):
        """Test case for creating a title with invalid data.

        This test case tests that a 400 status code is returned when
        an invalid movieOrTv value is provided.
        """
        data = {
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "invalid",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('"Invalid" Is Not A Valid Choice.', response.data["error"])

    def test_title_viewset_create_invalid_genres(self):
        """Test case for creating a title with invalid genres.

        This test case tests that a 400 status code is returned when
        an invalid genre value is provided.
        """
        data = {
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
            "genres": "invalid",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            'Expected A List Of Items But Got Type "Str".', response.data["error"]
        )

    def test_title_viewset_create_genre_not_exist(self):
        """Test case for creating a title with genres that do not exist.

        This test case tests that a 400 status code is returned when
        an invalid genre value is provided.
        """
        data = {
            "title": "Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an movie.",
            "imgUrl": "http://example.com/movie.jpg",
            "movieOrTv": "movie",
            "genres": [10, 15],
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            'Invalid Pk "10" - Object Does Not Exist.', response.data["error"]
        )

    def test_title_viewset_update_without_token(self):
        """
        Test case for updating a title without authentication.

        This test case tests that a 401 status code is returned when
        a title is updated without authentication.
        """
        self.client.credentials()  # Remove token
        data = {
            "title": "Updated Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an updated movie.",
            "imgUrl": "http://example.com/updated_movie.jpg",
            "movieOrTv": "movie",
        }
        response = self.client.put(
            self.detail_url(pk=self.title.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            "Authentication Credentials Were Not Provided.",
            response.data["error"],
        )

    def test_title_viewset_update_not_staff(self):
        """
        Test case for updating a title as a non-staff user.

        This test case tests that a 403 status code is returned when
        a title is updated as a non-staff user.
        """
        data = {
            "title": "Updated Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an updated movie.",
            "imgUrl": "http://example.com/updated_movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.put(
            self.detail_url(pk=self.title.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_title_viewset_update_staff(self):
        """
        Test case for updating a title as a staff user.

        This test case tests that a 200 status code is returned when
        a title is updated as a staff user.
        """
        data = {
            "title": "Updated Movie",
            "releaseDate": "2022-01-01",
            "overview": "This is an updated movie.",
            "imgUrl": "http://example.com/updated_movie.jpg",
            "movieOrTv": "movie",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.put(
            self.detail_url(pk=self.title.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.title.refresh_from_db()
        self.assertEqual(self.title.title, "Updated Movie")
        self.assertEqual(self.title.release_date, datetime.date(2022, 1, 1))
        self.assertEqual(self.title.overview, "This is an updated movie.")
        self.assertEqual(self.title.img_url, "http://example.com/updated_movie.jpg")
        self.assertEqual(self.title.movie_or_tv, "movie")

    def test_title_viewset_delete_without_token(self):
        """
        Test case for deleting a title without authentication.

        This test case tests that a 401 status code is returned when
        a title is deleted without authentication.
        """
        self.client.credentials()  # Remove token
        response = self.client.delete(self.detail_url(pk=self.title.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            "Authentication Credentials Were Not Provided.",
            response.data["error"],
        )

    def test_title_viewset_delete_not_staff(self):
        """
        Test case for deleting a title as a non-staff user.

        This test case tests that a 403 status code is returned when
        a title is deleted as a non-staff user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.delete(self.detail_url(pk=self.title.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_title_viewset_delete_staff(self):
        """
        Test case for deleting a title as a staff user.

        This test case tests that a 204 status code is returned when
        a title is deleted as a staff user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.delete(self.detail_url(pk=self.title.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Title.objects.filter(pk=self.title.pk).exists())

    def test_title_viewset_detail_without_token(self):
        """
        Test case for retrieving a title without authentication.

        This test case tests that a 200 status code is returned when
        a title is retrieved without authentication.
        """
        self.client.credentials()  # Remove token
        response = self.client.get(self.detail_url(pk=self.title.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_title_viewset_detail_not_found(self):
        """Test case for retrieving a title that does not exist.

        This test case tests that a 404 status code is returned when
        a title is retrieved that does not exist.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.get(self.detail_url(pk=9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual("Not Found.", response.data["error"])

    def test_title_viewset_list_without_token(self):
        """
        Test case for listing titles without authentication.

        This test case tests that a 200 status code is returned when
        titles are listed without authentication.
        """
        self.client.credentials()  # Remove token
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertIsInstance(
            response.data["results"], list
        )  # Check if response data is a list


class TestTitleViewSetFilters(BaseTestViewSet):
    """
    Test cases for the TitleViewSet.

    This class contains tests for various actions on the TitleViewSet Filters, including:
    - Test filter by title search
    - Test filter by genre
    - Test filter by rating
    - Test filter by year range

    """

    @classmethod
    def setUpTestData(cls):
        """
        Create test data for the test cases.

        Sets up the test data for the test cases in this class. This includes creating four titles with different genres and years, and creating reviews for each title to test the rating filter.

        The test data is as follows:

        - Action Movie (1992)
        - Comedy Movie (1991)
        - Action TV (1990)
        - Comedy TV (1993)

        Each title has a review with a rating of 5, 4, 3, or 2, respectively.

        """
        cls.url_name = "title"
        super().setUpTestData()

        # Create test data
        cls.titles = [
            cls.create_title(
                cls,
                "Action Movie",
                "movie",
                datetime.date(1992, 1, 1),
                "This is an action movie.",
                "http://example.com/action_movie.jpg",
                "Action",
                None,
            ),
            cls.create_title(
                cls,
                "Comedy Movie",
                "movie",
                datetime.date(1991, 1, 1),
                "This is an comedy movie.",
                "http://example.com/comedy_movie.jpg",
                "Comedy",
                None,
            ),
            cls.create_title(
                cls,
                "Action Tv",
                "tv",
                datetime.date(1990, 1, 1),
                "This is an action Tv show.",
                "http://example.com/action_tv.jpg",
                "Action",
                None,
            ),
            cls.create_title(
                cls,
                "Comedy Tv",
                "tv",
                datetime.date(1993, 1, 1),
                "This is an comedy Tv show.",
                "http://example.com/comedy_tv.jpg",
                "Comedy",
                None,
            ),
        ]

        # Create reviews for the titles for rating purposes
        for rating, title in zip([5, 4, 3, 2], cls.titles):
            cls.create_review(cls, title, rating)

    def test_filter_by_title_search(self):
        response = self.client.get(self.list_url, {"search": "Action"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        # The results should be ordered by -rating (default) unless specified otherwise
        self.assertEqual(
            response.data["results"][0]["title"], "Action Movie"
        )  # Rating 5
        self.assertEqual(response.data["results"][1]["title"], "Action Tv")  # Rating 4

    def test_filter_by_genre(self):
        genre = Genre.objects.get(genre_name="Action")
        response = self.client.get(self.list_url, {"genres": genre.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        # Ensure results are ordered by -rating by default
        self.assertEqual(
            response.data["results"][0]["title"], "Action Movie"
        )  # Rating 5
        self.assertEqual(response.data["results"][1]["title"], "Action Tv")  # Rating 4

    def test_filter_by_rating_range(self):
        response = self.client.get(self.list_url, {"ratingRange": "2,4"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
        # Ensure results are ordered by -rating (default)
        self.assertEqual(
            response.data["results"][0]["title"], "Comedy Movie"
        )  # Rating 4
        self.assertEqual(response.data["results"][1]["title"], "Action Tv")  # Rating 3
        self.assertEqual(response.data["results"][2]["title"], "Comedy Tv")  # Rating 2

    def test_filter_by_rating_range_invalid_format(self):
        response = self.client.get(self.list_url, {"ratingRange": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Invalid Range Format, Must Be 'Start,End'"
        )

    def test_filter_by_rating_range_not_integers(self):
        response = self.client.get(self.list_url, {"ratingRange": "a,b"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Both Range Values Must Be Integers")

    def test_filter_by_rating_range_min_greater_than_max(self):
        response = self.client.get(self.list_url, {"ratingRange": "5,4"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Start Range Must Be Less Than Or Equal To End Range",
        )

    def test_filter_by_rating_range_max_out_of_range(self):
        response = self.client.get(self.list_url, {"ratingRange": "5,11"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "The Range Must Be Between 0 And 10")

    def test_filter_by_rating_range_min_out_of_range(self):
        response = self.client.get(self.list_url, {"ratingRange": "-1,1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "The Range Must Be Between 0 And 10")

    def test_filter_by_rating_range_min_and_max_out_of_range(self):
        response = self.client.get(self.list_url, {"ratingRange": "-1,11"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "The Range Must Be Between 0 And 10")

    def test_filter_by_year_range(self):
        response = self.client.get(self.list_url, {"yearRange": "1990,1991"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        # Ensure results are ordered by -rating (default)
        self.assertEqual(
            response.data["results"][0]["title"], "Comedy Movie"
        )  # Rating 4
        self.assertEqual(response.data["results"][1]["title"], "Action Tv")  # Rating 3

    def test_filter_by_year_range_invalid_format(self):
        response = self.client.get(self.list_url, {"yearRange": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Invalid Year Range Format. Expected 'Startyear,Endyear'",
        )

    def test_filter_by_year_range_not_integers(self):
        response = self.client.get(self.list_url, {"yearRange": "a,b"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Both Year Range Values Must Be Integers"
        )

    def test_filter_by_year_range_start_greater_than_end(self):
        response = self.client.get(self.list_url, {"yearRange": "1991,1990"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Start Year Must Be Less Than Or Equal To End Year"
        )

    def test_filter_by_year_range_start_out_of_range(self):
        response = self.client.get(self.list_url, {"yearRange": "-1,1991"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Years Must Be Positive And Less Than Or Equal To The Current Year",
        )

    def test_filter_by_year_range_end_out_of_range(self):
        response = self.client.get(self.list_url, {"yearRange": "1990,2025"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Years Must Be Positive And Less Than Or Equal To The Current Year",
        )

    def test_order_by_title(self):
        response = self.client.get(self.list_url, {"orderBy": "title"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        # Ensure results are ordered alphabetically by title (ascending)
        self.assertEqual(response.data["results"][0]["title"], "Action Movie")
        self.assertEqual(response.data["results"][1]["title"], "Action Tv")
        self.assertEqual(response.data["results"][2]["title"], "Comedy Movie")
        self.assertEqual(response.data["results"][3]["title"], "Comedy Tv")

    def test_order_by_rating(self):
        response = self.client.get(self.list_url, {"orderBy": "rating"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        # Ensure results are ordered by rating in ascending order
        self.assertEqual(response.data["results"][0]["title"], "Comedy Tv")  # Rating 2
        self.assertEqual(response.data["results"][1]["title"], "Action Tv")  # Rating 3
        self.assertEqual(
            response.data["results"][2]["title"], "Comedy Movie"
        )  # Rating 4
        self.assertEqual(
            response.data["results"][3]["title"], "Action Movie"
        )  # Rating 5

    def test_order_by_release_date(self):
        response = self.client.get(self.list_url, {"orderBy": "release_date"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        # Ensure results are ordered by release_date in ascending order
        self.assertEqual(response.data["results"][0]["title"], "Action Tv")  # 1990
        self.assertEqual(response.data["results"][1]["title"], "Comedy Movie")  # 1991
        self.assertEqual(response.data["results"][2]["title"], "Action Movie")  # 1992
        self.assertEqual(response.data["results"][3]["title"], "Comedy Tv")  # 1993

    def test_order_by_invalid_field(self):
        """
        Test that an invalid order by field returns an error
        """
        response = self.client.get(self.list_url, {"orderBy": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid Ordering Parameter: Invalid")

    def test_pagination_page_size(self):
        response = self.client.get(self.list_url, {"pageSize": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["count"], 4)

    def test_pagination_page_size_all(self):
        response = self.client.get(self.list_url, {"pageSize": "all"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        self.assertEqual(response.data["count"], 4)

    def test_pagination_page_size_invalid(self):
        """
        Test that an invalid page size returns an error
        """
        response = self.client.get(self.list_url, {"pageSize": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], 'Page Size Must Be An Integer Or "All"'
        )

    def test_pagination_page(self):
        response = self.client.get(self.list_url, {"pageSize": 2, "page": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["count"], 4)

    def test_pagination_page_invalid(self):
        """
        Test that an invalid page number returns an error
        """
        response = self.client.get(self.list_url, {"pageSize": 2, "page": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Invalid Page.")

    def test_pagination_page_out_of_range(self):
        response = self.client.get(self.list_url, {"pageSize": 2, "page": 3})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Invalid Page.")

    def test_pagination_all(self):
        response = self.client.get(self.list_url, {"pageSize": "all"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        self.assertEqual(response.data["count"], 4)


class TestGenreViewSet(BaseTestViewSet):
    """
    Test case for the GenreViewSet.

    This class contains tests for various actions on the GenreViewSet, including:
    - Retrieving a genre without authentication
    - Listing genres without authentication
    - Creating a genre without authentication
    - Creating a genre as a non-staff user
    - Creating a genre as a staff user
    - Updating a genre without authentication
    - Updating a genre as a non-staff user
    - Updating a genre as a staff user
    - Deleting a genre without authentication
    - Deleting a genre as a non-staff user
    - Deleting a genre as a staff user
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for the test case.

        This method is called once before all the test cases.
        It sets the url_name attribute to "genre" and calls the
        setUpTestData method of the superclass.
        It then creates a new genre and assigns it to the genre attribute of the class.
        """

        cls.url_name = "genre"
        super().setUpTestData()
        cls.genre = cls.create_genre(cls, "New Genre")

    def test_genre_viewset_list(self):
        """
        Test case for listing genres.

        This test case tests that a 200 status code is returned when
        genres are listed.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertIsInstance(
            response.data["results"], list
        )  # Check if response data is a list

    def test_genre_viewset_detail(self):
        """
        Test case for retrieving a genre.

        This test case tests that a 200 status code is returned when
        a genre is retrieved.
        """
        response = self.client.get(self.detail_url(pk=self.genre.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["genreName"], self.genre.genre_name
        )  # Check the genre name

    def test_genre_viewset_create_without_token(self):
        """
        Test case for creating a genre without authentication.

        This test case tests that a 401 status code is returned when
        a genre is created without authentication.
        """
        self.client.credentials()  # Remove token
        data = {"genreName": "Drama"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            "Authentication Credentials Were Not Provided.",
            response.data["error"],
        )

    def test_genre_viewset_create_not_staff(self):
        """
        Test case for creating a genre as a non-staff user.

        This test case tests that a 403 status code is returned when
        a genre is created as a non-staff user.
        """
        data = {"genreName": "Drama"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_genre_viewset_create_staff(self):
        """
        Test case for creating a genre as a staff user.

        This test case tests that a 201 status code is returned when
        a genre is created as a staff user.
        """
        data = {"genreName": "Drama"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_genre = Genre.objects.get(genre_name="Drama")
        self.assertEqual(new_genre.genre_name, "Drama")

    def test_genre_viewset_update_without_token(self):
        """
        Test case for updating a genre without authentication.

        This test case tests that a 401 status code is returned when
        a genre is updated without authentication.
        """
        self.client.credentials()  # Remove token
        data = {"genreName": "Updated Genre"}
        response = self.client.put(
            self.detail_url(pk=self.genre.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            "Authentication Credentials Were Not Provided.",
            response.data["error"],
        )

    def test_genre_viewset_update_not_staff(self):
        """
        Test case for updating a genre as a non-staff user.

        This test case tests that a 403 status code is returned when
        a genre is updated as a non-staff user.
        """
        data = {"genreName": "Updated Genre"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.put(
            self.detail_url(pk=self.genre.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_genre_viewset_update_staff(self):
        """
        Test case for updating a genre as a staff user.

        This test case tests that a 200 status code is returned when
        a genre is updated as a staff user.
        """
        data = {"genreName": "Updated Genre"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.put(
            self.detail_url(pk=self.genre.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.genre.refresh_from_db()
        self.assertEqual(self.genre.genre_name, "Updated Genre")

    def test_genre_viewset_delete_without_token(self):
        """
        Test case for deleting a genre without authentication.

        This test case tests that a 401 status code is returned when
        a genre is deleted without authentication.
        """
        self.client.credentials()  # Remove token
        response = self.client.delete(self.detail_url(pk=self.genre.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            "Authentication Credentials Were Not Provided.",
            response.data["error"],
        )

    def test_genre_viewset_delete_not_staff(self):
        """
        Test case for deleting a genre as a non-staff user.

        This test case tests that a 403 status code is returned when
        a genre is deleted as a non-staff user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.delete(self.detail_url(pk=self.genre.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_genre_viewset_delete_staff(self):
        """
        Test case for deleting a genre as a staff user.

        This test case tests that a 204 status code is returned when
        a genre is deleted as a staff user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.delete(self.detail_url(pk=self.genre.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Genre.objects.filter(pk=self.genre.pk).exists())


class TestReviewViewSet(BaseTestViewSet):
    """
    Test case for ReviewViewSet.

    This class contains tests for various actions on the ReviewViewSet, including:
    - Retrieving a review without authentication
    - Listing review without authentication
    - Creating a review without authentication
    - Creating a review as authenticated user
    - Creating a review by the same user twice for the same title
    - Updating a review without authentication
    - Updating a review as the review's author
    - Updating a review as a staff user
    - Updating a review as not the author of the review
    - Deleting a review without authentication
    - Deleting a review as the review's author
    - Deleting a review as not the author of the review
    - Deleting a review as a staff user

    """

    @classmethod
    def setUpTestData(cls):
        """
        Setup the test data for the test cases.

        This method is called once before all the test cases.
        It sets the url_name attribute to "review" and calls the
        setUpTestData method of the superclass.
        It then creates a new title and assigns it to the title attribute of the class.
        Finally, it creates a new review and assigns it to the review attribute of the class.
        """
        cls.url_name = "review"
        super().setUpTestData()
        cls.title = cls.create_title(cls)
        cls.review = cls.create_review(cls, cls.title)

    def test_detail_review(self):
        """
        Test case for retrieving a review.

        This test case tests that a 200 status code is returned when
        a review is retrieved.
        """
        response = self.client.get(self.detail_url(pk=self.review.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.review.title.id)
        self.assertEqual(response.data["rating"], self.review.rating)
        self.assertEqual(response.data["comment"], self.review.comment)

    def test_list_review(self):
        """
        Test case for listing reviews.

        This test case tests that a 200 status code is returned when
        reviews are listed.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_review_without_token(self):
        """
        Test case for creating a review without authentication.

        This test case tests that a 401 status code is returned when
        a review is created without authentication.
        """
        self.client.credentials()  # Remove token
        data = {
            "title": self.title.id,
            "rating": 4.5,
            "comment": "Great movie!",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["error"], "Authentication Credentials Were Not Provided."
        )

    def test_create_review_authenticated_user(self):
        """
        Test case for creating a review as an authenticated user.

        - This test case tests that a 201 status code is returned when
        a review is created as an authenticated user.
        - And also tests that a 400 status code is returned when
        a review is created by the same user twice for the same title.
        """

        url = reverse("review-list")
        data = {
            "title": self.title.id,
            "rating": 4.5,
            "comment": "Great movie!",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "You Have Already Reviewed This Title. You Can Only Review Each Title Once.",
            response.data["error"],
        )

    def test_update_review_without_token(self):
        """
        Test case for updating a review without authentication.

        This test case tests that a 401 status code is returned when
        a review is updated without authentication.
        """
        self.client.credentials()  # Remove token
        data = {
            "title": self.title.id,
            "rating": 4.5,
            "comment": "Great movie!",
        }
        response = self.client.put(
            self.detail_url(pk=self.review.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["error"], "Authentication Credentials Were Not Provided."
        )

    def test_update_review_not_author(self):
        """
        Test case for updating a review as a user who is not the author.

        This test case tests that a 403 status code is returned when
        a review is updated as a user who is not the author.
        """
        data = {
            "title": self.title.id,
            "rating": 4.5,
            "comment": "Great movie!",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")
        response = self.client.put(
            self.detail_url(pk=self.review.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_update_review_staff(self):
        """
        Test case for updating a review as a staff user.

        This test case tests that a 403 status code is returned when
        a review is updated as a staff user.
        """
        data = {
            "title": self.title.id,
            "rating": 5.0,
            "comment": "Very Great movie!",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.put(
            self.detail_url(pk=self.review.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )

    def test_update_review_author(self):
        """
        Test case for updating a review as an author.

        This test case tests that a 200 status code is returned when
        a review is updated as an author.
        """
        data = {
            "title": self.title.id,
            "rating": 5.0,
            "comment": "Very Great movie!",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.put(
            self.detail_url(pk=self.review.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5.0)
        self.assertEqual(self.review.comment, "Very Great movie!")

    def test_delete_review_without_token(self):
        """
        Test case for deleting a review without authentication.

        This test case tests that a 401 status code is returned when
        a review is deleted without authentication.
        """
        self.client.credentials()  # Remove token
        response = self.client.delete(self.detail_url(pk=self.review.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["error"], "Authentication Credentials Were Not Provided."
        )

    def test_delete_review_staff(self):
        """
        Test case for deleting a review as a staff user.

        This test case tests that a 403 status code is returned when
        a review is deleted as a staff user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")
        response = self.client.delete(self.detail_url(pk=self.review.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_author(self):
        """
        Test case for deleting a review as an author.

        This test case tests that a 204 status code is returned when
        a review is deleted as an author.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.delete(self.detail_url(pk=self.review.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_not_author(self):
        """
        Test case for deleting a review as a user who is not the author.

        This test case tests that a 403 status code is returned when
        a review is deleted as a user who is not the author.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")
        response = self.client.delete(self.detail_url(pk=self.review.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            "You Do Not Have Permission To Perform This Action.",
            response.data["error"],
        )


class TestUserViewSet(BaseTestViewSet):
    """
    Tests for the UserViewSet class.
    """

    url_name = "user"

    def test_create_user_valid_token(self):
        """
        Test creating a new user with a valid token.
        """
        # Create a validation token for the user
        token_entry = ValidationToken.objects.create(
            email="newuser@example.com", token="validtoken"
        )

        # User creation data with the token
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "token": "validtoken",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user is created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "newuser@example.com")

        # Ensure the token is deleted after creation
        self.assertFalse(ValidationToken.objects.filter(token="validtoken").exists())

    def test_create_user_invalid_token(self):
        """
        Test creating a new user with an invalid token.
        """
        # User creation data with an invalid token
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "token": "invalidtoken",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid Or Expired Token.")

    def test_create_user_expired_token(self):
        """
        Test creating a new user with an expired token.
        """
        # Create a validation token for the user
        token_entry = ValidationToken.objects.create(
            email="newuser@example.com",
            token="expiredtoken",
        )
        token_entry.created_at -= timedelta(minutes=3)
        token_entry.save()

        # User creation data with an expired token
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "token": "expiredtoken",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid Or Expired Token.")

    def test_create_user_no_token(self):
        """
        Test creating a new user without a token.
        """
        # User creation data without a token
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Token Is Required.")

    def test_create_user_no_password(self):
        """
        Test creating a new user without a password.
        """
        # Create a validation token for the user
        token_entry = ValidationToken.objects.create(
            email="newuser@example.com", token="validtoken"
        )

        # User creation data without a password
        data = {
            "token": "validtoken",
            "email": "newuser@example.com",
            "username": "newuser",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Password Is Required.")

    def test_create_user_no_email(self):
        """
        Test creating a new user without an email.
        """
        # User creation data without an email
        data = {
            "username": "newuser",
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Email Is Required.")

    def test_create_user_invalid_email(self):
        """
        Test creating a new user with an invalid email.
        """
        # User creation data with an invalid email
        data = {
            "email": "invalidemail",
            "username": "newuser",
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Enter A Valid Email Address.")

    def test_create_user_existing_email(self):
        """
        Test creating a new user with an existing email.
        """
        # User creation data with an existing email
        data = {
            "email": self.user.email,
            "username": "newuser",
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "User With This Email Already Exists.")

    def test_create_user_no_username(self):
        """
        Test creating a new user without a username.
        """
        # User creation data without a username
        data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Username Is Required.")

    def test_create_user_invalid_username(self):
        """
        Test creating a new user with an invalid username.
        """
        # Create a validation token for the user
        token_entry = ValidationToken.objects.create(
            email="newuser@example.com", token="validtoken"
        )
        # User creation data with an invalid username
        data = {
            "token": "validtoken",
            "email": "newuser@example.com",
            "username": "invalidusername$",
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Enter A Valid Username. This Value May Contain Only Letters, Numbers, And @/./+/-/_ Characters.",
        )

    def test_create_user_existing_username(self):
        """
        Test creating a new user with an existing username.
        """
        # User creation data with an existing username
        data = {
            "email": "newuser@example.com",
            "username": self.user.username,
            "password": "newpassword123",
        }

        # Make POST request to create the user
        response = self.client.post(self.list_url, data)

        # Assert that user creation fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "A User With That Username Already Exists."
        )

    def test_update_user_as_current_user(self):
        """
        Test updating the user's own information.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        data = {"username": "updateduser"}

        response = self.client.patch(self.detail_url(self.user.id), data)

        # Assert that update is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "updateduser")

    def test_update_user_as_other_user(self):
        """
        Test that a user cannot update another user's information.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")
        data = {"username": "updateduser"}

        response = self.client.patch(self.detail_url(self.user.id), data)

        # Assert that update is forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "You Do Not Have Permission To Perform This Action."
        )

    def test_retrieve_user_as_admin(self):
        """
        Test retrieving user details as an admin.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")

        response = self.client.get(self.detail_url(self.user.id))

        # Assert that retrieve is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_retrieve_user_as_other_user(self):
        """
        Test that a user cannot retrieve another user's details.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        response = self.client.get(self.detail_url(self.user.id))

        # Assert that retrieve is forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "You Do Not Have Permission To Perform This Action."
        )

    def test_delete_user_as_admin(self):
        """
        Test deleting a user as an admin.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}")

        response = self.client.delete(self.detail_url(self.user.id))

        # Assert that delete is successful
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_delete_user_as_non_admin(self):
        """
        Test that a non-admin user cannot delete another user.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_access_token}")

        response = self.client.delete(self.detail_url(self.user.id))

        # Assert that delete is forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestValidationViewSet(APITestCase):
    """
    Test cases for validation token creation and sending email.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpassword"
        )
        cls.url_name = "validation"
        cls.list_url = reverse(f"{cls.url_name}-list")
        cls.detail_url = lambda *args, **kwargs: f"{cls.url_name}-detail"

    def setUp(self):
        self.client = APIClient()

    def test_create_validation_token_register(self):
        """
        Test creating a validation token and sending the email.
        """
        data = {"email": "newtestuser@example.com", "type": "register"}

        with patch("app.api.views.send_mail") as mock_send_mail:
            response = self.client.post(self.list_url, data, format="json")

            # Verify token creation
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(
                ValidationToken.objects.filter(email="newtestuser@example.com").exists()
            )

            # Verify email sent
            mock_send_mail.assert_called_once()

    def test_create_validation_token_register_existing_email(self):
        """
        Test creating a validation token for an existing email.

        This test case tests that a 400 status code is returned when
        a validation token is created for an existing email.
        """
        data = {"email": "testuser@example.com", "type": "register"}

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Email Already Exists.", response.data["error"])

    def test_create_validation_token_reset_password(self):
        """
        Test creating a validation token and sending the email.

        This test case tests that a 200 status code is returned when
        a validation token is created and the email is sent.
        """
        data = {"email": "testuser@example.com", "type": "reset_password"}

        with patch("app.api.views.send_mail") as mock_send_mail:
            response = self.client.post(self.list_url, data, format="json")

            # Verify token creation
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(
                ValidationToken.objects.filter(email="testuser@example.com").exists()
            )

            # Verify email sent
            mock_send_mail.assert_called_once()

    def test_create_validation_token_reset_password_not_found(self):
        """
        Test creating a validation token for an email not in the system.

        This test case tests that a 400 status code is returned when
        a validation token is created for an email not in the system.
        """
        data = {"email": "notfound@example.com", "type": "reset_password"}

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Email Not Found.", response.data["error"])


class TestPasswordResetViewSet(APITestCase):
    """
    Test case for password reset view.

    This class contains tests for the password reset view:
    - Test resetting the password with a valid token
    - Test resetting the password with an invalid token
    - Test resetting the password with an invalid email
    - Test resetting the password with an invalid password

    """

    @classmethod
    def setUpTestData(cls):
        """
        Setup the test data for the test cases.

        This method is called once before all the test cases.
        It creates a test user and sets the url_name, list_url, and detail_url
        attributes of the class.
        """
        cls.user = User.objects.create_user(
            email="testuser@example.com", password="password123", username="testuser"
        )
        cls.url_name = "password_reset"
        cls.list_url = reverse(f"{cls.url_name}-list")
        cls.detail_url = lambda *args, **kwargs: f"{cls.url_name}-detail"

    def setUp(self):
        """
        Setup the client and create a validation token for the test user.

        This method is called once before each test case.
        It sets the client attribute of the class to an APIClient instance
        and creates a validation token for the test user.
        The validation token is saved to the validation_token attribute of the class.
        """
        self.client = APIClient()

        self.validation_token = ValidationToken.objects.create(
            email=self.user.email, token="valid_token"
        )

    @patch("app.api.views.ValidationToken.objects.get")
    def test_reset_password_with_valid_token(self, mock_token_get):
        """
        Test resetting the password with a valid token.

        This test case tests that a 200 status code is returned when
        a password is reset with a valid token.
        """
        mock_token_get.return_value = self.validation_token
        data = {
            "email": self.user.email,
            "token": "valid_token",
            "newPassword": "newpassword123",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify password change
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

        # Verify token is deleted
        self.assertFalse(ValidationToken.objects.filter(token="valid_token").exists())

    def test_reset_password_with_invalid_token(self):
        """
        Test resetting the password with an invalid token.

        This test case tests that a 400 status code is returned when
        a password is reset with an invalid token.
        """
        data = {
            "email": self.user.email,
            "token": "invalid_token",
            "newPassword": "newpassword123",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid Or Expired Token.", response.data["error"])

    def test_reset_password_with_invalid_email(self):
        """
        Test resetting the password with an email that does not exist.

        This test case tests that a 400 status code is returned when
        a password is reset with an invalid email.
        """
        data = {
            "email": "notfound@example.com",
            "token": "valid_token",
            "newPassword": "newpassword123",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email Not Found.", response.data["error"])

    def test_reset_password_with_short_password(self):
        """
        Test resetting the password with a short password.

        This test case tests that a 400 status code is returned when
        a password is reset with a short password.
        """
        data = {
            "email": self.user.email,
            "token": "valid_token",
            "newPassword": "short",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Ensure New Password Has At Least 8 Characters.", response.data["error"]
        )


class TestAuthViewSet(APITestCase):
    """
    Test case for auth view.

    This class contains tests for the auth view:
    - Test Google login with a valid token
    - Test Google login with an invalid token
    - Test Google login with an invalid email"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com", password="password123", username="testuser"
        )
        cls.url = reverse("auth-google-login")

    def setUp(self):
        self.client = APIClient()

    @patch("app.api.views.id_token.verify_oauth2_token")
    def test_google_login_success(self, mock_verify_token):
        """
        Test Google login with a valid token.

        This test case tests that a 200 status code is returned when
        a user is logged in with a valid token.
        """
        mock_verify_token.return_value = {
            "email": "testuser@example.com",
            "given_name": "Test",
            "family_name": "User",
        }

        data = {"credential": "valid_credential"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Verify token of the user
        token = AccessToken(response.data["access"])
        self.assertEqual(int(token["user_id"]), self.user.id)

    @patch("app.api.views.id_token.verify_oauth2_token")
    def test_google_signup_success(self, mock_verify_token):
        """
        Test Google login with a valid token.

        This test case tests that a 200 status code is returned when
        a user is logged in with a valid token.
        """
        mock_verify_token.return_value = {
            "email": "newtestuser@example.com",
            "given_name": "Test",
            "family_name": "User",
        }

        data = {"credential": "valid_credential"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Verify user creation
        self.assertTrue(User.objects.filter(email="newtestuser@example.com").exists())
        new_user = User.objects.get(email="newtestuser@example.com")
        # Verify token of the user
        token = AccessToken(response.data["access"])
        self.assertEqual(int(token["user_id"]), new_user.id)

    @patch("app.api.views.id_token.verify_oauth2_token")
    def test_google_login_invalid_token(self, mock_verify_token):
        """
        Test Google login with an invalid token.

        This test case tests that a 400 status code is returned when
        a user is logged in with an invalid token.
        """
        mock_verify_token.side_effect = ValueError("Invalid Credentials")

        data = {"credential": "invalid_credential"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid Credentials")


class CustomTokenObtainPairViewTests(APITestCase):
    """
    Test case for token_obtain_pair view.

    This class contains tests for the token_obtain_pair view:
    - Test successful login resets failed attempts
    - Test failed login increments failed attempts
    - Test invalid login attempts reset failed attempts
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword",
            username="testuser",
        )
        cls.url = reverse("token_obtain_pair")

    def setUp(self):
        """
        Setup the test case.

        This method creates a test user and a client for testing
        """

        self.client = APIClient()

    def test_successful_login_resets_failed_attempts(self):
        """
        Test that a successful login resets failed login attempts.

        This test case tests that a successful login resets the failed login
        attempts counter. It logs in the user with a valid email and password
        and checks that the failed_login_attempts field is reset to 0.
        """
        response = self.client.post(
            self.url, {"email": "testuser@example.com", "password": "testpassword"}
        )
        self.assertEqual(response.status_code, 200)

        # Reload user from the database and check failed attempts reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_failed_login_increments_failed_attempts(self):
        """
        Test that a failed login increments failed login attempts.

        This test case tests that a failed login increments the failed login
        attempts counter. It logs in the user with a valid email and an
        incorrect password and checks that the failed_login_attempts field is
        incremented by one.
        """
        response = self.client.post(
            self.url,
            {"email": "testuser@example.com", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized

        # Reload user from the database and check failed attempts increment
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)
        self.assertEqual(
            response.data["error"],
            f"No Active Account Found With The Given Credentials",
        )

    def test_account_locks_after_max_failed_attempts(self):
        """
        Test that an account locks after the maximum number of failed login attempts.

        This test case tests that an account locks after the maximum number of
        failed login attempts. It simulates the maximum number of failed login
        attempts and checks that the is_locked field is True and the lock_until
        field is set to a future date.
        """
        for _ in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
            self.client.post(
                self.url,
                {"email": "testuser@example.com", "password": "wrongpassword"},
            )

        # Reload user and check if account is locked
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)
        self.assertIsNotNone(self.user.lock_until)
        self.assertTrue(self.user.lock_until > timezone.now())

    def test_cannot_login_when_account_is_locked(self):
        """
        Test that a user cannot login when their account is locked.

        This test case tests that a user cannot login when their account is locked due
        to multiple failed login attempts. It locks the user manually and then attempts
        to login with correct credentials. It checks that the response status code is
        401 (Unauthorized) and that the error message contains the correct message.
        """
        self.user.is_locked = True
        self.user.lock_until = timezone.now() + timedelta(minutes=5)
        self.user.save()

        # Attempt login with correct credentials while account is locked
        response = self.client.post(
            self.url, {"email": "testuser@example.com", "password": "testpassword"}
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        self.assertEqual(
            response.data["error"],
            "Your Account Has Been Locked Due To Multiple Failed Login Attempts.",
        )

    def test_login_succeeds_after_lock_expires(self):
        """
        Test that a user can login after their account lock has expired.

        This test case tests that a user can login after their account lock has expired.
        It locks the user manually with a lock_until date set to the past, then attempts
        to login with correct credentials. It checks that the response status code is
        200 (OK) and that the is_locked field is False and the failed_login_attempts
        field is reset to 0.
        """
        self.user.is_locked = True
        self.user.lock_until = timezone.now() - timedelta(minutes=1)
        self.user.save()

        # Attempt login with correct credentials after lock expires
        response = self.client.post(
            self.url, {"email": "testuser@example.com", "password": "testpassword"}
        )
        self.assertEqual(response.status_code, 200)

        # Reload user and ensure the lock is removed and attempts are reset
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked)
        self.assertEqual(self.user.failed_login_attempts, 0)
