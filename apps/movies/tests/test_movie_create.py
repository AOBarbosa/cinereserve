import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.movies.models import Movie
from apps.movies.tests.factories import MovieFactory
from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"


@pytest.fixture
def movie_list_url():
    return reverse("movie-list")


@pytest.fixture
def valid_payload():
    movie = MovieFactory.build(
        title="Inception",
        description="A mind-bending thriller.",
        release_year=2010,
        duration=148,
        genre="Sci-Fi",
        director="Christopher Nolan",
        rating="8.8",
    )
    return {
        "title": movie.title,
        "description": movie.description,
        "release_year": movie.release_year,
        "duration": movie.duration,
        "genre": movie.genre,
        "director": movie.director,
        "rating": str(movie.rating),
    }


def make_client(is_staff=False):
    client = APIClient()
    user = UserFactory(is_staff=is_staff)
    user.set_password(PASSWORD)
    user.save()
    client.post(
        reverse("user-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    return client


@pytest.fixture
def admin_client():
    return make_client(is_staff=True)


@pytest.fixture
def regular_client():
    return make_client(is_staff=False)


@pytest.mark.django_db
class TestMovieCreate:
    def test_admin_can_create_movie(self, admin_client, movie_list_url, valid_payload):
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_movie_persists_to_db(
        self, admin_client, movie_list_url, valid_payload
    ):
        admin_client.post(movie_list_url, valid_payload, format="json")

        assert Movie.objects.filter(title=valid_payload["title"]).exists()

    def test_create_movie_returns_expected_fields(
        self, admin_client, movie_list_url, valid_payload
    ):
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.data["title"] == valid_payload["title"]
        assert response.data["director"] == valid_payload["director"]
        assert "id" in response.data
        assert response.data["is_active"] is True

    def test_regular_user_cannot_create_movie(
        self, regular_client, movie_list_url, valid_payload
    ):
        response = regular_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_create_movie(
        self, movie_list_url, valid_payload
    ):
        response = APIClient().post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_movie_missing_title(
        self, admin_client, movie_list_url, valid_payload
    ):
        del valid_payload["title"]
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data

    def test_create_movie_missing_release_year(
        self, admin_client, movie_list_url, valid_payload
    ):
        del valid_payload["release_year"]
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "release_year" in response.data

    def test_create_movie_missing_duration(
        self, admin_client, movie_list_url, valid_payload
    ):
        del valid_payload["duration"]
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "duration" in response.data

    def test_create_movie_without_rating(
        self, admin_client, movie_list_url, valid_payload
    ):
        del valid_payload["rating"]
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rating"] is None

    def test_create_movie_without_description(
        self, admin_client, movie_list_url, valid_payload
    ):
        del valid_payload["description"]
        response = admin_client.post(movie_list_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["description"] == ""
