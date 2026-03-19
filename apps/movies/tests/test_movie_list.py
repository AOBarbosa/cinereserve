import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.movies.models import Movie
from apps.movies.tests.factories import MovieFactory
from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def movie_list_url():
    return reverse("movie-list")


@pytest.fixture
def auth_client():
    client = APIClient()
    user = UserFactory()
    user.set_password(PASSWORD)
    user.save()
    client.post(
        reverse("user-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    return client


@pytest.mark.django_db
class TestMovieList:
    def test_unauthenticated_user_can_list_movies(self, client, movie_list_url):
        MovieFactory.create_batch(3)

        response = client.get(movie_list_url)

        assert response.status_code == status.HTTP_200_OK

    def test_authenticated_user_can_list_movies(self, auth_client, movie_list_url):
        MovieFactory.create_batch(3)

        response = auth_client.get(movie_list_url)

        assert response.status_code == status.HTTP_200_OK

    def test_returns_all_movies(self, client, movie_list_url):
        MovieFactory.create_batch(5)

        response = client.get(movie_list_url)

        assert response.data["count"] == 5

    def test_returns_empty_list_when_no_movies(self, client, movie_list_url):
        response = client.get(movie_list_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_response_is_paginated(self, client, movie_list_url):
        MovieFactory.create_batch(3)

        response = client.get(movie_list_url)

        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    def test_response_contains_expected_fields(self, client, movie_list_url):
        MovieFactory()

        response = client.get(movie_list_url)

        movie = response.data["results"][0]
        assert "id" in movie
        assert "title" in movie
        assert "description" in movie
        assert "release_year" in movie
        assert "duration" in movie
        assert "genre" in movie
        assert "director" in movie
        assert "rating" in movie
        assert "is_active" in movie

    def test_password_not_exposed(self, client, movie_list_url):
        MovieFactory()

        response = client.get(movie_list_url)

        movie = response.data["results"][0]
        assert "created_at" not in movie
        assert "updated_at" not in movie

    def test_movies_ordered_by_release_year_desc(self, client, movie_list_url):
        MovieFactory(title="Old Movie", release_year=2000)
        MovieFactory(title="New Movie", release_year=2024)
        MovieFactory(title="Newest Movie", release_year=2025)

        response = client.get(movie_list_url)

        years = [m["release_year"] for m in response.data["results"]]
        assert years == sorted(years, reverse=True)

    def test_pagination_page_size(self, client, movie_list_url):
        MovieFactory.create_batch(25)

        response = client.get(movie_list_url)

        assert len(response.data["results"]) == 20
        assert response.data["count"] == 25
        assert response.data["next"] is not None

    def test_pagination_second_page(self, client, movie_list_url):
        MovieFactory.create_batch(25)

        response = client.get(movie_list_url, {"page": 2})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_movie_count_reflects_db(self, client, movie_list_url):
        MovieFactory.create_batch(3)

        response = client.get(movie_list_url)

        assert response.data["count"] == Movie.objects.count()

    def test_inactive_movies_hidden_from_unauthenticated(self, client, movie_list_url):
        MovieFactory(is_active=True)
        MovieFactory(is_active=False)

        response = client.get(movie_list_url)

        assert response.data["count"] == 1

    def test_inactive_movies_hidden_from_regular_users(
        self, auth_client, movie_list_url
    ):
        MovieFactory(is_active=True)
        MovieFactory(is_active=False)

        response = auth_client.get(movie_list_url)

        assert response.data["count"] == 1

    def test_admin_sees_all_movies_including_inactive(self, movie_list_url):
        admin = APIClient()
        user = UserFactory(is_staff=True)
        user.set_password(PASSWORD)
        user.save()
        admin.post(
            reverse("user-login"),
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        MovieFactory(is_active=True)
        MovieFactory(is_active=False)

        response = admin.get(movie_list_url)

        assert response.data["count"] == 2
