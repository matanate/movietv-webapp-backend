from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        from .models import Genre
        import requests
        import os

        # TMDB API key
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        API_HEADERS = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}",
        }

        # TMDB API URLs
        URL_MOVIE_GENRES = "https://api.themoviedb.org/3/genre/movie/list?language=en"
        URL_TV_GENRES = "https://api.themoviedb.org/3/genre/tv/list?language=en"

        # Fetching movie and TV genres from TMDB API
        try:
            movie_genres = requests.get(URL_MOVIE_GENRES, headers=API_HEADERS).json()[
                "genres"
            ]
            tv_genres = requests.get(URL_TV_GENRES, headers=API_HEADERS).json()[
                "genres"
            ]

            # Populate or create Genre instances
            for genre in movie_genres + tv_genres:
                Genre.objects.update_or_create(
                    id=genre["id"], defaults={"genre_name": genre["name"]}
                )
        except requests.RequestException as e:
            print(f"Error fetching genres from TMDB API: {e}")
            raise
