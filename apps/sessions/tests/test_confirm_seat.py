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


def confirm_url(movie_id, session_id, seat_id):
    return reverse(
        "seat-confirm",
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
def reserved_seat(session, user):
    seat = session.seats.first()
    seat.status = Seat.Status.RESERVED
    seat.save()
    Reservation.objects.create(
        user=user,
        seat=seat,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    return seat


@pytest.mark.django_db
class TestConfirmSeatView:
    def test_unauthenticated_user_gets_401(self, session, reserved_seat):
        client = APIClient()

        response = client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_confirm_valid_reservation_returns_200(self, auth_client, session, reserved_seat):
        response = auth_client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        assert response.status_code == status.HTTP_200_OK

    def test_confirm_sets_seat_status_to_purchased(self, auth_client, session, reserved_seat):
        auth_client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        reserved_seat.refresh_from_db()
        assert reserved_seat.status == Seat.Status.PURCHASED

    def test_confirm_sets_is_confirmed_true(self, auth_client, session, reserved_seat):
        auth_client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        reservation = Reservation.objects.get(seat=reserved_seat)
        assert reservation.is_confirmed is True

    def test_confirm_removes_redis_lock(self, auth_client, session, reserved_seat):
        cache.add(f"seat_lock:{reserved_seat.id}", 999, timeout=600)

        auth_client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        assert cache.get(f"seat_lock:{reserved_seat.id}") is None

    def test_response_contains_expected_fields(self, auth_client, session, reserved_seat):
        response = auth_client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        assert "id" in response.data
        assert "seat" in response.data
        assert "expires_at" in response.data
        assert "is_confirmed" in response.data

    def test_expired_reservation_returns_400(self, auth_client, user, session):
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()
        Reservation.objects.create(
            user=user,
            seat=seat,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = auth_client.post(confirm_url(session.movie_id, session.id, seat.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_expired_reservation_reverts_seat_to_available(self, auth_client, user, session):
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()
        Reservation.objects.create(
            user=user,
            seat=seat,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        auth_client.post(confirm_url(session.movie_id, session.id, seat.id))

        seat.refresh_from_db()
        assert seat.status == Seat.Status.AVAILABLE

    def test_expired_reservation_is_deleted(self, auth_client, user, session):
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()
        Reservation.objects.create(
            user=user,
            seat=seat,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        auth_client.post(confirm_url(session.movie_id, session.id, seat.id))

        assert not Reservation.objects.filter(seat=seat).exists()

    def test_other_user_cannot_confirm_reservation(self, session, reserved_seat):
        other_user = UserFactory()
        other_user.set_password(PASSWORD)
        other_user.save()
        other_client = APIClient()
        other_client.post(
            reverse("user-login"),
            {"email": other_user.email, "password": PASSWORD},
            format="json",
        )

        response = other_client.post(confirm_url(session.movie_id, session.id, reserved_seat.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_seat_without_reservation_returns_404(self, auth_client, session):
        seat = session.seats.last()

        response = auth_client.post(confirm_url(session.movie_id, session.id, seat.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_already_confirmed_reservation_returns_404(self, auth_client, user, session):
        seat = session.seats.first()
        seat.status = Seat.Status.PURCHASED
        seat.save()
        Reservation.objects.create(
            user=user,
            seat=seat,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_confirmed=True,
        )

        response = auth_client.post(confirm_url(session.movie_id, session.id, seat.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_seat_from_different_session_returns_404(self, auth_client, session, user):
        other_session = MovieSessionFactory(rows=1, columns=1)
        other_seat = other_session.seats.first()
        other_seat.status = Seat.Status.RESERVED
        other_seat.save()
        Reservation.objects.create(
            user=user,
            seat=other_seat,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = auth_client.post(confirm_url(session.movie_id, session.id, other_seat.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND
