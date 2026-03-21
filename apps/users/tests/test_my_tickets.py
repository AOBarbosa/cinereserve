from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.sessions.models import Reservation, Seat
from apps.sessions.tests.factories import MovieSessionFactory
from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"
MY_TICKETS_URL = reverse("my-tickets")


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


def make_confirmed_reservation(user, start_time=None, end_time=None):
    """Helper to create a confirmed reservation with full session context."""
    now = timezone.now()
    session = MovieSessionFactory(
        rows=1,
        columns=1,
        start_time=start_time or now + timedelta(days=1),
        end_time=end_time or now + timedelta(days=1, hours=2),
    )
    seat = session.seats.first()
    seat.status = Seat.Status.PURCHASED
    seat.save()
    return Reservation.objects.create(
        user=user,
        seat=seat,
        expires_at=now + timedelta(minutes=10),
        is_confirmed=True,
    )


@pytest.mark.django_db
class TestMyTicketsView:
    def test_unauthenticated_user_gets_401(self):
        response = APIClient().get(MY_TICKETS_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_gets_200(self, auth_client):
        response = auth_client.get(MY_TICKETS_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_response_is_paginated(self, auth_client):
        response = auth_client.get(MY_TICKETS_URL)

        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    def test_returns_only_confirmed_tickets(self, auth_client, user):
        make_confirmed_reservation(user)
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        Reservation.objects.create(
            user=user,
            seat=seat,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_confirmed=False,
        )

        response = auth_client.get(MY_TICKETS_URL)

        assert response.data["count"] == 1

    def test_returns_only_current_user_tickets(self, auth_client, user):
        other_user = UserFactory()
        make_confirmed_reservation(user)
        make_confirmed_reservation(other_user)

        response = auth_client.get(MY_TICKETS_URL)

        assert response.data["count"] == 1

    def test_returns_empty_list_when_no_tickets(self, auth_client):
        response = auth_client.get(MY_TICKETS_URL)

        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_response_contains_expected_fields(self, auth_client, user):
        make_confirmed_reservation(user)

        response = auth_client.get(MY_TICKETS_URL)

        ticket = response.data["results"][0]
        assert "id" in ticket
        assert "ticket_code" in ticket
        assert "movie_title" in ticket
        assert "session_room" in ticket
        assert "session_start_time" in ticket
        assert "session_end_time" in ticket
        assert "seat_row" in ticket
        assert "seat_column" in ticket
        assert "created_at" in ticket

    def test_upcoming_filter_returns_future_sessions(self, auth_client, user):
        now = timezone.now()
        make_confirmed_reservation(user, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        make_confirmed_reservation(user, start_time=now - timedelta(days=1), end_time=now - timedelta(hours=22))

        response = auth_client.get(MY_TICKETS_URL, {"upcoming": "true"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["session_start_time"] > now.isoformat()

    def test_upcoming_false_returns_past_sessions(self, auth_client, user):
        now = timezone.now()
        make_confirmed_reservation(user, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        make_confirmed_reservation(user, start_time=now - timedelta(days=1), end_time=now - timedelta(hours=22))

        response = auth_client.get(MY_TICKETS_URL, {"upcoming": "false"})

        assert response.data["count"] == 1
        assert response.data["results"][0]["session_start_time"] < now.isoformat()

    def test_no_filter_returns_all_confirmed_tickets(self, auth_client, user):
        now = timezone.now()
        make_confirmed_reservation(user, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        make_confirmed_reservation(user, start_time=now - timedelta(days=1), end_time=now - timedelta(hours=22))

        response = auth_client.get(MY_TICKETS_URL)

        assert response.data["count"] == 2

    def test_tickets_ordered_by_session_start_time_descending(self, auth_client, user):
        now = timezone.now()
        make_confirmed_reservation(user, start_time=now + timedelta(days=3), end_time=now + timedelta(days=3, hours=2))
        make_confirmed_reservation(user, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=2))
        make_confirmed_reservation(user, start_time=now + timedelta(days=2), end_time=now + timedelta(days=2, hours=2))

        response = auth_client.get(MY_TICKETS_URL)

        start_times = [t["session_start_time"] for t in response.data["results"]]
        assert start_times == sorted(start_times, reverse=True)
