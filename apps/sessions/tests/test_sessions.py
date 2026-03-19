from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.movies.tests.factories import MovieFactory
from apps.sessions.tests.factories import MovieSessionFactory


def session_list_url(movie_id):
    return reverse("movie-session-list", kwargs={"movie_id": movie_id})


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
class TestMovieSessionList:
    def test_unauthenticated_user_can_list_sessions(self, client):
        movie = MovieFactory()
        MovieSessionFactory(movie=movie)

        response = client.get(session_list_url(movie.id))

        assert response.status_code == status.HTTP_200_OK

    def test_response_is_paginated(self, client):
        movie = MovieFactory()
        MovieSessionFactory(movie=movie)

        response = client.get(session_list_url(movie.id))

        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    def test_returns_only_sessions_for_requested_movie(self, client):
        movie = MovieFactory()
        other_movie = MovieFactory()
        MovieSessionFactory.create_batch(2, movie=movie)
        MovieSessionFactory(movie=other_movie)

        response = client.get(session_list_url(movie.id))

        assert response.data["count"] == 2

    def test_only_active_sessions_are_returned(self, client):
        movie = MovieFactory()
        MovieSessionFactory(movie=movie, is_active=True)
        MovieSessionFactory(movie=movie, is_active=False)

        response = client.get(session_list_url(movie.id))

        assert response.data["count"] == 1

    def test_returns_empty_list_when_no_sessions(self, client):
        movie = MovieFactory()

        response = client.get(session_list_url(movie.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_returns_empty_list_for_nonexistent_movie(self, client):
        response = client.get(session_list_url(99999))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_response_contains_expected_fields(self, client):
        movie = MovieFactory()
        MovieSessionFactory(movie=movie)

        response = client.get(session_list_url(movie.id))

        session = response.data["results"][0]
        assert "id" in session
        assert "room" in session
        assert "start_time" in session
        assert "end_time" in session
        assert "price" in session
        assert "is_active" in session

    def test_internal_fields_not_exposed(self, client):
        movie = MovieFactory()
        MovieSessionFactory(movie=movie)

        response = client.get(session_list_url(movie.id))

        session = response.data["results"][0]
        assert "movie" not in session
        assert "rows" not in session
        assert "columns" not in session

    def test_sessions_ordered_by_start_time(self, client):
        movie = MovieFactory()
        now = timezone.now()
        MovieSessionFactory(
            movie=movie,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=5),
        )
        MovieSessionFactory(
            movie=movie,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        MovieSessionFactory(
            movie=movie,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=4),
        )

        response = client.get(session_list_url(movie.id))

        start_times = [s["start_time"] for s in response.data["results"]]
        assert start_times == sorted(start_times)

    def test_inactive_sessions_from_other_movies_not_leaked(self, client):
        movie = MovieFactory()
        other_movie = MovieFactory()
        MovieSessionFactory(movie=movie, is_active=True)
        MovieSessionFactory(movie=other_movie, is_active=False)

        response = client.get(session_list_url(movie.id))

        assert response.data["count"] == 1
        assert response.data["results"][0]["is_active"] is True
