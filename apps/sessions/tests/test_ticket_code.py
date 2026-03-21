from datetime import timedelta

import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
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


@pytest.mark.django_db
class TestTicketCode:
    def test_reservation_has_ticket_code_on_creation(self, user, session):
        seat = session.seats.first()
        reservation = Reservation.objects.create(
            user=user,
            seat=seat,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        assert reservation.ticket_code is not None

    def test_ticket_codes_are_unique_across_reservations(self, user, session):
        seats = list(session.seats.all()[:2])
        r1 = Reservation.objects.create(
            user=user, seat=seats[0], expires_at=timezone.now() + timedelta(minutes=10)
        )
        r2 = Reservation.objects.create(
            user=user, seat=seats[1], expires_at=timezone.now() + timedelta(minutes=10)
        )

        assert r1.ticket_code != r2.ticket_code

    def test_ticket_code_exposed_in_reserve_response(self, auth_client, session):
        seat = session.seats.first()

        response = auth_client.post(reserve_url(session.movie_id, session.id, seat.id))

        assert "ticket_code" in response.data
        assert response.data["ticket_code"] is not None

    def test_ticket_code_exposed_in_confirm_response(self, auth_client, session):
        seat = session.seats.first()
        auth_client.post(reserve_url(session.movie_id, session.id, seat.id))

        response = auth_client.post(confirm_url(session.movie_id, session.id, seat.id))

        assert "ticket_code" in response.data
        assert response.data["ticket_code"] is not None

    def test_ticket_code_is_same_after_confirmation(self, auth_client, session):
        seat = session.seats.first()
        reserve_response = auth_client.post(
            reserve_url(session.movie_id, session.id, seat.id)
        )
        confirm_response = auth_client.post(
            confirm_url(session.movie_id, session.id, seat.id)
        )

        assert reserve_response.data["ticket_code"] == confirm_response.data["ticket_code"]
