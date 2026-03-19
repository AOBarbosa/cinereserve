from django.urls import path

from apps.sessions.views import MovieSessionListView

urlpatterns = [
    path("", MovieSessionListView.as_view(), name="movie-session-list"),
]
