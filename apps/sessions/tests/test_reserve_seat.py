from datetime import timedelta

import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.sessions.models import Reservation, Seat
from apps.sessions.tests.factories import MovieSessionFactory
from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"


def reserve_url(movie_id, session_id, seat_id):
    return reverse(
        "seat-reserve",
        kwargs={"movie_id": movie_id, "session_id": session_id, "seat_id": seat_id},
    )


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    u = UserFactory()
    u.set_password(PASSWORD)
    u.save()
    return u


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.post(
        reverse("user-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    return client


@pytest.fixture
def session():
    return MovieSessionFactory(rows=2, columns=2)


@pytest.fixture
def available_seat(session):
    return session.seats.first()


@pytest.mark.django_db
class TestReserveSeatView:
    def test_unauthenticated_user_gets_401(self, session, available_seat):
        client = APIClient()

        response = client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reserve_available_seat_returns_200(self, auth_client, session, available_seat):
        response = auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert response.status_code == status.HTTP_200_OK

    def test_reserve_sets_seat_status_to_reserved(self, auth_client, session, available_seat):
        auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        available_seat.refresh_from_db()
        assert available_seat.status == Seat.Status.RESERVED

    def test_reserve_creates_reservation(self, auth_client, user, session, available_seat):
        auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert Reservation.objects.filter(seat=available_seat, user=user).exists()

    def test_reservation_expires_in_10_minutes(self, auth_client, session, available_seat):
        auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        reservation = Reservation.objects.get(seat=available_seat)
        expected_expiry = timezone.now() + timedelta(minutes=10)
        assert abs((reservation.expires_at - expected_expiry).total_seconds()) < 5

    def test_reservation_is_not_confirmed_on_creation(self, auth_client, session, available_seat):
        auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        reservation = Reservation.objects.get(seat=available_seat)
        assert reservation.is_confirmed is False

    def test_response_contains_expected_fields(self, auth_client, session, available_seat):
        response = auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert "id" in response.data
        assert "seat" in response.data
        assert "expires_at" in response.data
        assert "is_confirmed" in response.data

    def test_reserve_sets_redis_lock(self, auth_client, session, available_seat):
        auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert cache.get(f"seat_lock:{available_seat.id}") is not None

    def test_reserve_reserved_seat_returns_409(self, auth_client, session, available_seat):
        available_seat.status = Seat.Status.RESERVED
        available_seat.save()

        response = auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_reserve_purchased_seat_returns_409(self, auth_client, session, available_seat):
        available_seat.status = Seat.Status.PURCHASED
        available_seat.save()

        response = auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_redis_lock_prevents_double_booking(self, auth_client, session, available_seat):
        cache.add(f"seat_lock:{available_seat.id}", 999, timeout=600)

        response = auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_redis_lock_does_not_create_reservation(self, auth_client, session, available_seat):
        cache.add(f"seat_lock:{available_seat.id}", 999, timeout=600)

        auth_client.post(reserve_url(session.movie_id, session.id, available_seat.id))

        assert not Reservation.objects.filter(seat=available_seat).exists()

    def test_seat_from_different_session_returns_404(self, auth_client, session, available_seat):
        other_session = MovieSessionFactory(rows=1, columns=1)
        other_seat = other_session.seats.first()

        response = auth_client.post(reserve_url(session.movie_id, session.id, other_seat.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_seat_returns_404(self, auth_client, session):
        response = auth_client.post(reserve_url(session.movie_id, session.id, 99999))

        assert response.status_code == status.HTTP_404_NOT_FOUND
