import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.movies.models import Movie
from apps.movies.tests.factories import MovieFactory
from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"


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
def client():
    return APIClient()


@pytest.fixture
def admin_client():
    return make_client(is_staff=True)


@pytest.fixture
def regular_client():
    return make_client(is_staff=False)


@pytest.fixture
def movie():
    return MovieFactory()


@pytest.fixture
def inactive_movie():
    return MovieFactory(is_active=False)


def detail_url(pk):
    return reverse("movie-detail", kwargs={"pk": pk})


@pytest.mark.django_db
class TestMovieRetrieve:
    def test_anyone_can_retrieve_active_movie(self, client, movie):
        response = client.get(detail_url(movie.pk))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == movie.pk

    def test_non_admin_cannot_retrieve_inactive_movie(self, client, inactive_movie):
        response = client.get(detail_url(inactive_movie.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_retrieve_inactive_movie(self, admin_client, inactive_movie):
        response = admin_client.get(detail_url(inactive_movie.pk))

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMovieUpdate:
    def test_admin_can_fully_update_movie(self, admin_client, movie):
        payload = {
            "title": "Updated Title",
            "description": "Updated.",
            "release_year": 2023,
            "duration": 120,
            "genre": "Drama",
            "director": "New Director",
            "rating": "7.5",
        }

        response = admin_client.put(detail_url(movie.pk), payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        movie.refresh_from_db()
        assert movie.title == "Updated Title"
        assert movie.director == "New Director"

    def test_admin_can_partially_update_movie(self, admin_client, movie):
        response = admin_client.patch(detail_url(movie.pk), {"title": "Only Title Changed"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        movie.refresh_from_db()
        assert movie.title == "Only Title Changed"

    def test_regular_user_cannot_update_movie(self, regular_client, movie):
        response = regular_client.put(detail_url(movie.pk), {"title": "Hacked"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_update_movie(self, client, movie):
        response = client.patch(detail_url(movie.pk), {"title": "Hacked"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_nonexistent_movie_returns_404(self, admin_client):
        response = admin_client.patch(detail_url(9999), {"title": "Ghost"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMovieSoftDelete:
    def test_admin_can_delete_movie(self, admin_client, movie):
        response = admin_client.delete(detail_url(movie.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_sets_is_active_false(self, admin_client, movie):
        admin_client.delete(detail_url(movie.pk))

        movie.refresh_from_db()
        assert movie.is_active is False

    def test_deleted_movie_still_exists_in_db(self, admin_client, movie):
        admin_client.delete(detail_url(movie.pk))

        assert Movie.objects.filter(pk=movie.pk).exists()

    def test_deleted_movie_hidden_from_regular_users(self, admin_client, regular_client, movie):
        admin_client.delete(detail_url(movie.pk))

        response = regular_client.get(reverse("movie-list"))
        ids = [m["id"] for m in response.data["results"]]
        assert movie.pk not in ids

    def test_deleted_movie_hidden_from_unauthenticated_users(self, admin_client, client, movie):
        admin_client.delete(detail_url(movie.pk))

        response = client.get(reverse("movie-list"))
        ids = [m["id"] for m in response.data["results"]]
        assert movie.pk not in ids

    def test_deleted_movie_still_visible_to_admin(self, admin_client, movie):
        admin_client.delete(detail_url(movie.pk))

        response = admin_client.get(reverse("movie-list"))
        ids = [m["id"] for m in response.data["results"]]
        assert movie.pk in ids

    def test_regular_user_cannot_delete_movie(self, regular_client, movie):
        response = regular_client.delete(detail_url(movie.pk))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        movie.refresh_from_db()
        assert movie.is_active is True

    def test_unauthenticated_user_cannot_delete_movie(self, client, movie):
        response = client.delete(detail_url(movie.pk))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
