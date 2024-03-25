# from django.shortcuts import render, redirect
# from django.contrib.auth import get_user, authenticate, login
# from django.contrib.auth.models import User
# from django.contrib import messages
# from django.http import HttpResponseServerError
# from .forms import LoginForm, SignupForm
# from .models import Reviews, Titles
# import os
# import requests
# from datetime import datetime

# # API key and secret key
# API_KEY = os.environ.get("API_KEY")
# API_HEADERS = {
#     "accept": "application/json",
#     "Authorization": f"Bearer {API_KEY}",
# }

# # TMDB API URLs
# URL_MOVIE_GENERS = "https://api.themoviedb.org/3/genre/movie/list?language=en"
# URL_TV_GENERS = "https://api.themoviedb.org/3/genre/tv/list?language=en"

# # Set titles per page
# TITLES_PER_PAGE = 2

# # Fetching movie and TV genres from TMDB API
# movie_genres = requests.get(URL_MOVIE_GENERS, headers=API_HEADERS).json()["genres"]
# tv_genres = requests.get(URL_TV_GENERS, headers=API_HEADERS).json()["genres"]
# genres_dict = {}
# for genre in movie_genres:
#     genres_dict[genre["id"]] = genre["name"]
# for genre in tv_genres:
#     genres_dict[genre["id"]] = genre["name"]


# # Function to fetch titles from TMDB API based on search query
# def fetch_titles_from_api(movie_or_tv, title):
#     # Construct the API URL for searching titles based on the provided parameters
#     url = f"https://api.themoviedb.org/3/search/{movie_or_tv}?query={title}&include_adult=false&language=en-US&page=1"

#     try:
#         # Make a GET request to the TMDB API with the specified headers
#         response = requests.get(url, headers=API_HEADERS)

#         # Raise an exception for HTTP errors
#         response.raise_for_status()

#         # Parse the JSON response and extract the results
#         response = response.json()["results"]

#         # Initialize an empty list to store the extracted title information
#         titles_list = []

#         # Loop through each title in the API response
#         for title in response:
#             # Determine the key names based on the movie_or_tv parameter
#             if movie_or_tv == "movie":
#                 release_date_text = "release_date"
#                 title_text = "title"
#             elif movie_or_tv == "tv":
#                 release_date_text = "first_air_date"
#                 title_text = "name"

#             # Create a dictionary with relevant title information and append it to the list
#             titles_list.append(
#                 {
#                     "id": title["id"],
#                     "title": title[title_text],
#                     "release_date": title[release_date_text],
#                     "overview": title["overview"],
#                     "img_url": f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{title['poster_path']}",
#                     "genre_ids": title["genre_ids"],
#                 }
#             )
#             # Return the list of titles
#             return titles_list

#     # Handle exceptions related to the API request
#     except requests.RequestException as e:
#         print(f"Error during API request: {e}")
#         # Abort the request and return a 500 Internal Server Error status
#         return HttpResponseServerError(f"Internal Server Error: {e}")


# # Create your views here.
# def home(request):
#     # Query all titles from the database
#     all_titles = Titles.objects.all()

#     # Get the top 10 movies based on ratings
#     top_movies = Titles.objects.filter(movie_or_tv="movie").order_by("-ratings")[:10]

#     # Get the top 10 tv shows based on ratings
#     top_tvs = Titles.objects.filter(movie_or_tv="tv").order_by("-ratings")[:10]

#     # Create a dictionary with top movies and TV shows
#     top_titles = {"Movies": top_movies, "TV Shows": top_tvs}

#     # Render the homepage template with title information
#     return render(
#         request,
#         "homepage.html",
#         context={
#             "all_titles": all_titles,
#             "top_titles": top_titles,
#         },
#     )


# # Route for user signup
# def signup(request):
#     if request.method == "POST":
#         # Fetch the signup form from the request object
#         form = SignupForm(request.POST)

#         if form.is_valid():
#             # Retrieve user input from the signup form
#             name = form.cleaned_data["InputName"]
#             email = form.cleaned_data["InputEmail"]
#             password = form.cleaned_data["InputPassword"]
#             user = User.objects.get(email=email)

#             # Check if the user with the given email already exists
#             if user:
#                 # If the user already exists, flash a warning and redirect to the login page
#                 messages.warning(request, f"That email already exist, please Login.")
#                 return redirect("login")
#             else:
#                 # Create a new user and add them to the database
#                 user = User.objects.create_user(name, email, password)

#                 # Log in the newly created user
#                 login(user)

#                 # Redirect to the homepage
#                 return redirect("home")
#     else:
#         form = SignupForm()

#     # Render the signup form template
#     return render(request, "signup.html", {"form": form})


# # Route for user login
# def login(request):
#     if request.method == "POST":
#         # Fetch the signup form from the request object
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             # Retrieve user input from the login form
#             email = form.cleaned_data["InputEmail"]
#             password = form.cleaned_data["InputPassword"]

#             # Use the query method to get the user object
#             user = authenticate(request, email=email, password=password)

#             if not user:
#                 # If the user does not exist, flash a warning and redirect to the login page
#                 messages.warning("That email does not exist, please try again.")
#                 return redirect("login")
#             elif not check_password_hash(user.password, password):
#                 # If the password is incorrect, flash a warning and redirect to the login page
#                 flash("Password incorrect, please try again.", "warning")
#                 return redirect(url_for("login"))
#             else:
#                 # If login is successful, log in the user and redirect to the homepage
#                 login_user(user)
#                 flash(f"Welcome {user.name}, you are now logged in.", "success")
#                 return redirect(url_for("home"))
#         else:
#             form = LoginForm()

#     # Render the login form template
#     return render(request, "login.html", {"form": form})


# # Route for user logout
# def logout():
#     if not current_user.is_authenticated:
#         # Redirect to the homepage
#         return redirect(url_for("home"))
#     # Flash a logout message, log out the user, and redirect to the homepage
#     flash(f"Goodbye {current_user.name}, you are now logged out.", "success")
#     logout_user()
#     return redirect(url_for("home"))
