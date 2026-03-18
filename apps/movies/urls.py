from django.urls import path

from apps.movies.views import MovieDetailView, MovieListView

urlpatterns = [
    path("", MovieListView.as_view(), name="movie-list"),
    path("<int:pk>/", MovieDetailView.as_view(), name="movie-detail"),
]
