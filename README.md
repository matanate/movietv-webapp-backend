### MovieTV App Backend

#### Overview

This Django-based backend serves as the API for the MovieTV app, now enhanced with viewsets, Google login/signup features, and email verification for signup and password reset. It provides RESTful endpoints for various functionalities, including user authentication, title management, review creation, and integration with the TMDB API for title data retrieval.

The backend utilizes JWT authentication with the `rest_framework_simplejwt` library, allowing users to obtain and refresh authentication tokens securely. Additionally, Google OAuth integration enables streamlined user authentication and profile management.

The project is organized into multiple Django apps, each handling specific aspects of the application, such as user management (`users` app), API endpoints (`app` app), and project configuration (`django_movietv`). The backend is designed to be flexible, supporting PostgreSQL or SQLite3 as the database backend, and uses environment variables for configuration, including database credentials and the TMDB API key.

**Note**: The app includes middleware that automatically converts between camel case (used by the frontend) and snake case (used by the backend), ensuring seamless integration between the two.

#### Installation and Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:

   ```bash
   cd <project-directory>
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   - Create a `.env` file with the following variables:

   ```bash
   DJANGO_SECRET_KEY=<your-secret-key>
   TMDB_API_KEY=<your-tmdb-api-key>
   DJANGO_SETTINGS_MODULE=django_movietv.dev_settings  # or prod_settings.py for production
   GOOGLE_CLIENT_ID=<your-google-client-id>
   EMAIL_HOST=<your-email-host>
   EMAIL_PORT=<your-email-port>
   EMAIL_HOST_USER=<your-email-host-user>
   DEFAULT_FROM_EMAIL=<your-default-from-email>
   EMAIL_HOST_PASSWORD=<your-email-host-password>
   ```

   - Export environment variables for development:

   ```bash
   export $(grep -v '^#' .env | xargs)
   ```

5. Configure Django settings:

   - For development, use `django_movietv.dev_settings`.
   - For production, use `django_movietv.prod_settings`.

6. Set `ALLOWED_HOSTS`:

   - Update the `ALLOWED_HOSTS` setting in your settings file to allow appropriate hosts.

#### Usage

1. Run migrations:

   ```bash
   python manage.py migrate
   ```

2. Start the development server:

   ```bash
   python manage.py runserver
   ```

#### API Endpoints

- `/token/`:

  - **POST**: Obtain JWT token for authentication
    - **Example**:
      ```json
      POST /token/
      {
        "username": "user",
        "password": "pass"
      }
      ```

- `/token/refresh/`:

  - **POST**: Refresh JWT token
    - **Example**:
      ```json
      POST /token/refresh/
      {
        "refresh": "your-refresh-token"
      }
      ```

- `/users/`:

  - **GET**: List users
  - **POST**: Create a new user
    - **Example**:
      ```json
      POST /users/
      {
        "username": "newuser",
        "password": "newpassword",
        "email": "newuser@example.com"
      }
      ```

- `/users/<int:user_id>/`:

  - **GET**: Retrieve a specific user
    - **Example**: `/users/1/` to get details of the user with ID 1
  - **PATCH**: Update user details
    - **Example**:
      ```json
      PATCH /users/1/
      {
        "email": "updateduser@example.com"
      }
      ```
  - **DELETE**: Delete a user
    - **Example**: `/users/1/` to delete the user with ID 1

- `/genres/`:

  - **GET**: List genres
    - **Example**: `/genres/` to get a list of all genres
    - **Example**: `/genres/?page=1` to get the first page of genres

- `/titles/`:

  - **GET**: List titles
    - **Example**: `/titles/?page=1` to get the first page of titles
    - **Example**: `/titles/?movie_or_tv=movie` to get only movies (first page as default)
    - **Example**: `/titles/?year_range=2000,2020` to get titles released between 2000 and 2020
    - **Example**: `/titles/?rating_range=4,8` to get titles with ratings between 4 and 8
    - **Example**: `/titles/?search=Inception` to search for titles containing "Inception"
    - **Example**: `/titles/?genres=1,2` to get titles that match genres with IDs 1 and 2
  - **POST**: Create a new title
    - **Example**:
      ```json
      POST /titles/
      {
        "title": "New Movie",
        "release_date": "2023-01-01",
        "rating": 7.5,
        "movie_or_tv": "movie",
        "genres": [1, 2]
      }
      ```

- `/titles/<int:title_id>/`:

  - **GET**: Retrieve a specific title
    - **Example**: `/titles/1/` to get details of the title with ID 1
  - **PATCH**: Update a title
    - **Example**:
      ```json
      PATCH /titles/1/
      {
        "rating": 8.0
      }
      ```
  - **DELETE**: Delete a title
    - **Example**: `/titles/1/` to delete the title with ID 1

- `/reviews/`:

  - **POST**: Create a review
    - **Example**:
      ```json
      POST /reviews/
      {
        "title": 1,
        "rating": 5,
        "review_text": "Great movie!"
      }
      ```

- `/reviews/<int:review_id>/`:

  - **PATCH**: Edit a review
    - **Example**:
      ```json
      PATCH /reviews/1/
      {
        "review_text": "Updated review text."
      }
      ```

- `/tmdb-search/`:

  - **GET**: Search titles in TMDB
    - **Example**: `/tmdb-search/?query=Inception` to search for titles with "Inception"

- `/password-reset/`:

  - **POST**: Reset password
    - **Example**:
      ```json
      POST /password-reset/
      {
        "email": "user@example.com"
      }
      ```

- `/validation/`:

  - **POST**: Validate data
    - **Example**:
      ```json
      POST /validation/
      {
        "data": {
          "key": "value"
        }
      }
      ```

- `/auth/`:
  - **POST**: Google login authentication
    - **Example**:
      ```json
      POST /auth/google/
      {
        "credential": "your-google-oauth-token"
      }
      ```
    - **Response**:
      ```json
      {
        "refresh": "your-refresh-token",
        "access": "your-access-token"
      }
      ```
    - **Error Response**:
      ```json
      {
        "error": "Invalid token"
      }
      ```

#### Dependencies

- Django: The core framework for building the web application.
- Django REST framework: For building the RESTful API.
- django_filters: To provide filtering capabilities for API queries.
- `rest_framework_simplejwt`: For handling JWT authentication and token management.
- PostgreSQL: Preferred database backend for production. SQLite3 can be used for development.
- google.oauth2: For Google OAuth integration and authentication.

#### Production Setup

1. A `Dockerfile` is available for setting up the production environment.

#### Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin feature/your-feature-name`).
6. Create a new Pull Request.

#### License

This project is licensed under the MIT License. See the LICENSE file for details.
