from datetime import date

from app.models import Genre, Review, Title
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class TitleModelTest(TestCase):
    """
    Test the Title model.

    This class defines the test suite for the Title model.
    - Test if the title is created successfully.
    - Test if genres were assigned correctly.
    - Test the __str__ method of Title model.
    """

    def setUp(self):
        """
        Set up a sample title for testing.
        """
        # Create some genres and titles for testing
        self.genre1 = Genre.objects.create(genre_name="Action")
        self.genre2 = Genre.objects.create(genre_name="Comedy")

        self.title = Title.objects.create(
            title="Test Movie",
            release_date=date.today(),
            overview="This is a test movie.",
            img_url="http://example.com/movie.jpg",
            movie_or_tv="movie",
        )

        # Add genres to the title
        self.title.genres.add(self.genre1, self.genre2)

    def test_title_creation(self):
        """
        Test if the title is created successfully.
        """
        self.assertEqual(self.title.title, "Test Movie")
        self.assertEqual(self.title.release_date, date.today())
        self.assertEqual(self.title.overview, "This is a test movie.")
        self.assertEqual(self.title.movie_or_tv, "movie")

    def test_title_genres(self):
        """
        Test if genres were assigned correctly.
        """
        genres = self.title.genres.all()
        self.assertIn(self.genre1, genres)
        self.assertIn(self.genre2, genres)

    def test_str_method(self):
        """
        Test the __str__ method of Title model.
        """
        self.assertEqual(str(self.title), "Test Movie")


class ReviewModelTest(TestCase):
    """
    Test the Review model.

    This class defines the test suite for the Review model.
    - Test if the review is created successfully.
    - Test if the review author is set correctly.
    - Test if the review title is set correctly.
    - Test the __str__ method of Review model.
    """

    def setUp(self):
        """
        Set up a sample review for testing.
        """
        self.user = User.objects.create_user(
            email="testuser@example.com", password="password123", username="testuser"
        )
        self.title = Title.objects.create(
            title="Test Movie",
            release_date=date.today(),
            overview="This is a test movie.",
            img_url="http://example.com/movie.jpg",
            movie_or_tv="movie",
        )
        self.review = Review.objects.create(
            author=self.user, rating=4.5, comment="Great movie!", title=self.title
        )

    def test_review_creation(self):
        """
        Test if the review is created successfully.
        """
        self.assertEqual(self.review.rating, 4.5)
        self.assertEqual(self.review.comment, "Great movie!")
        self.assertEqual(self.review.author, self.user)
        self.assertEqual(self.review.title, self.title)

    def test_str_method(self):
        """
        Test the __str__ method of Review model.

        The __str__ method of Review model should return a string with the
        following format: "Review by <username> on <title>".
        """
        expected_str = f"Review by {self.user.username} on {self.title.title}"
        self.assertEqual(str(self.review), expected_str)


class TitleAverageRatingTest(TestCase):
    """
    Test the TitleAverageRating model.

    This class defines the test suite for the TitleAverageRating model.
    - Test if the title average rating is calculated correctly.
    - Test if the __str__ method of TitleAverageRating model is correct.
    - Test if the update_average_rating_on_review_save_signal updates the
    average rating correctly.
    """

    def setUp(self):
        """
        Create a user, a title, and reviews for testing.

        This function creates two users and a title, and creates two reviews
        for the title, one by each user. The first review has a rating of 4.0
        and the second review has a rating of 5.0.
        """
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="password123", username="user1"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="password123", username="user2"
        )
        self.title = Title.objects.create(
            title="Test Movie",
            release_date=date.today(),
            overview="This is a test movie.",
            img_url="http://example.com/movie.jpg",
            movie_or_tv="movie",
        )
        self.review1 = Review.objects.create(
            author=self.user1, rating=4.0, comment="Good movie", title=self.title
        )
        self.review2 = Review.objects.create(
            author=self.user2, rating=5.0, comment="Awesome movie!", title=self.title
        )

    def test_average_rating_calculation(self):
        """
        Test if the average rating is calculated correctly.

        This test case tests that the average rating of a title is calculated
        correctly. It creates two reviews for the title, one with a rating of 4.0
        and the other with a rating of 5.0, and checks if the average rating of
        the title is 4.5.
        """
        self.title.update_average_rating()
        self.assertEqual(self.title.rating, 4.5)

    def test_update_average_rating_on_review_save_signal(self):
        """
        Test if the average rating updates when a review is saved.

        This test case tests that the average rating of a title is updated
        correctly when a review is saved. It creates two reviews for the title,
        updates one of the reviews with a rating of 3.0, and checks if the
        average rating of the title is 4.0.
        """

        self.review1.rating = 3.0
        self.review1.save()
        self.title.refresh_from_db()
        self.assertEqual(self.title.rating, 4.0)

    def test_update_average_rating_on_review_delete_signal(self):
        """
        Test if the average rating updates when a review is deleted.

        This test case tests that the average rating of a title is updated
        correctly when a review is deleted. It creates two reviews for the title,
        deletes one of the reviews, and checks if the average rating of the title
        is 4.0.
        """
        self.review2.delete()
        self.title.refresh_from_db()
        self.assertEqual(self.title.rating, 4.0)  # Only review1 remains, rating is 4.0


class GenreModelTest(TestCase):
    """
    Test the Genre model.

    This class defines the test suite for the Genre model.
    - Test if the genre is created successfully.
    - Test if the __str__ method of Genre model is correct.
    """

    def setUp(self):
        """
        Set up a sample genre for testing.

        This function is called once before each test case.
        It initializes the test genre for testing.
        """
        self.genre = Genre.objects.create(genre_name="Action")

    def test_genre_creation(self):
        """
        Test if the genre is created successfully.

        This test case tests that a genre is created successfully by comparing
        the genre name of the created genre with the expected genre name.
        """
        self.assertEqual(self.genre.genre_name, "Action")

    def test_str_method(self):
        """
        Test the __str__ method of Genre model.

        This test case tests that the __str__ method of the Genre model returns
        the correct string representation of the genre.
        """
        self.assertEqual(str(self.genre), "Action")


class UserModelTest(TestCase):
    """
    Test the User model.

    This class defines the test suite for the User model.
    - Test if the user is created successfully.
    - Test if the __str__ method of User model is correct.
    """

    def setUp(self):
        """
        Create a user for testing.

        This function is called once before each test case.
        It initializes the test user for testing.
        """
        self.user = User.objects.create_user(
            email="testuser@example.com", username="testuser", password="password123"
        )

    def test_create_user(self):
        """
        Test if the user is created successfully.

        This test case tests that a user is created successfully by comparing
        the email, username and password of the created user with the expected
        values.
        """
        self.assertEqual(self.user.email, "testuser@example.com")
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("password123"))

    def test_email_is_unique(self):
        """
        Test that email uniqueness is enforced.

        This test case tests that creating a user with the same email as an
        existing user raises an exception.
        """
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="testuser@example.com",
                username="anotheruser",
                password="password456",
            )

    def test_login_with_email(self):
        """
        Test if login can be done using the email field.

        This test case tests that the User.USERNAME_FIELD is set to 'email',
        which is the field that is used for authentication.
        """
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields(self):
        """
        Test that 'username' is a required field alongside 'email'.

        This test case tests that creating a user without a username raises an
        exception, and that creating a user with a username and an email
        successfully creates a user.
        """
        user = User.objects.create_user(
            email="anotheruser@example.com",
            username="anotheruser",
            password="password123",
        )
        self.assertEqual(user.email, "anotheruser@example.com")
        self.assertEqual(user.username, "anotheruser")

    def test_superuser_creation(self):
        """
        Test the creation of a superuser.

        This test case tests that a superuser can be created using the
        create_superuser method of the User model.
        """
        superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="admin123"
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_user_str_method(self):
        """
        Test the __str__ method of the CustomUser model.

        This test case tests that the __str__ method of the CustomUser model
        returns the email of the user.
        """
        self.assertEqual(str(self.user), self.user.email)
