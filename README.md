### MovieTV App Backend

#### Overview

This Django-based backend serves as the API for the MovieTV app. It provides RESTful endpoints for various functionalities, including user authentication, title management, review creation, and integration with the TMDB API for title data retrieval.

The backend utilizes JWT authentication with the `rest_framework_simplejwt` library, allowing users to obtain and refresh authentication tokens securely. It also implements a custom user model, which uses email addresses instead of usernames for authentication.

The project structure is organized into multiple Django apps, each handling specific aspects of the application, such as user management (`users` app), API endpoints (`app` app), and project configuration (`django_movietv`).

Additionally, the backend is designed to be flexible, with the ability to use either PostgreSQL or SQLite3 as the database backend. Environment variables are used for configuration, including database credentials and the TMDB API key.

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

- For PostgreSQL:
  ```
  DATABASE_NAME
  DATABASE_USER
  DATABASE_PASSWORD
  DATABASE_HOST
  ```
- For TMDB API:
  ```
  TMDB_API_KEY
  ```

5. Configure Django settings:

- For development, can update the `DATABASES` setting in `django_movietv/settings.py` to use SQLite3.

6. Set `FORCE_SCRIPT_NAME`:

- In development, remove `FORCE_SCRIPT_NAME = '/backend'` from `django_movietv/settings.py`.
- In production use if needed

7. Set `ALLOWED_HOSTS`:

- Update the `ALLOWED_HOSTS` setting in `django_movietv/settings.py` to allow appropriate hosts.

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

- /api/token/: Obtain JWT token for authentication
- /api/token/refresh/: Refresh JWT token
- /api/create-user/: Create a new user
- /api/genres/: Get genres
- /api/years/: Get years
- /api/titles/: Get titles
- /api/titles/<int:title_id>/: Get a specific title
- /api/reviews/: Create a review
- /api/reviews/<int:review_id>/: Edit a review
- /api/tmdb-search/: Search titles in TMDB
- /api/titles/add/: Add a title
- /api/titles/delete/<int:title_id>/: Delete a title
- /api/reviews/delete/<int:review_id>/: Delete a review

#### Dependencies

- Django
- Django REST framework
- `rest_framework_simplejwt`
- PostgreSQL (or SQLite3 for development)

#### Production Setup

1. Dockerfile is available

#### Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/your-feature-name).
3. Make your changes.
4. Commit your changes (git commit -am 'Add some feature').
5. Push to the branch (git push origin feature/your-feature-name).
6. Create a new Pull Request.

#### License

This project is licensed under the MIT License. See the LICENSE file for details.
