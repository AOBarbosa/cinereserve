from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.movies.tests.factories import MovieFactory
from apps.sessions.models import Reservation, Seat
from apps.sessions.tests.factories import MovieSessionFactory
from apps.users.tests.factories import UserFactory


def seat_map_url(movie_id, session_id):
    return reverse("seat-map", kwargs={"movie_id": movie_id, "session_id": session_id})


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
class TestSeatMapView:
    def test_unauthenticated_user_can_view_seat_map(self, client):
        session = MovieSessionFactory()

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert response.status_code == status.HTTP_200_OK

    def test_response_is_not_paginated(self, client):
        session = MovieSessionFactory()

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert isinstance(response.data, list)

    def test_returns_all_seats_for_session(self, client):
        session = MovieSessionFactory(rows=3, columns=4)

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert len(response.data) == 12  # 3 × 4

    def test_response_contains_expected_fields(self, client):
        session = MovieSessionFactory(rows=1, columns=1)

        response = client.get(seat_map_url(session.movie_id, session.id))

        seat = response.data[0]
        assert "id" in seat
        assert "row" in seat
        assert "column" in seat
        assert "status" in seat

    def test_all_new_seats_are_available(self, client):
        session = MovieSessionFactory(rows=2, columns=2)

        response = client.get(seat_map_url(session.movie_id, session.id))

        statuses = [s["status"] for s in response.data]
        assert all(s == Seat.Status.AVAILABLE for s in statuses)

    def test_reserved_seat_shows_reserved_status(self, client):
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert response.data[0]["status"] == Seat.Status.RESERVED

    def test_purchased_seat_shows_purchased_status(self, client):
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        seat.status = Seat.Status.PURCHASED
        seat.save()

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert response.data[0]["status"] == Seat.Status.PURCHASED

    def test_expired_reservation_reverts_seat_to_available(self, client):
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()
        Reservation.objects.create(
            user=UserFactory(),
            seat=seat,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert response.data[0]["status"] == Seat.Status.AVAILABLE

    def test_expired_reservation_is_deleted_after_lazy_expiry(self, client):
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()
        Reservation.objects.create(
            user=UserFactory(),
            seat=seat,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        client.get(seat_map_url(session.movie_id, session.id))

        assert not Reservation.objects.filter(seat=seat).exists()

    def test_confirmed_reservation_not_affected_by_lazy_expiry(self, client):
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        seat.status = Seat.Status.PURCHASED
        seat.save()
        Reservation.objects.create(
            user=UserFactory(),
            seat=seat,
            expires_at=timezone.now() - timedelta(minutes=1),
            is_confirmed=True,
        )

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert response.data[0]["status"] == Seat.Status.PURCHASED

    def test_non_expired_reservation_is_not_cleaned_up(self, client):
        session = MovieSessionFactory(rows=1, columns=1)
        seat = session.seats.first()
        seat.status = Seat.Status.RESERVED
        seat.save()
        Reservation.objects.create(
            user=UserFactory(),
            seat=seat,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert response.data[0]["status"] == Seat.Status.RESERVED

    def test_returns_only_seats_for_requested_session(self, client):
        session = MovieSessionFactory(rows=2, columns=2)
        MovieSessionFactory(rows=3, columns=3)

        response = client.get(seat_map_url(session.movie_id, session.id))

        assert len(response.data) == 4  # 2 × 2, not 4 + 9

    def test_returns_empty_list_for_nonexistent_session(self, client):
        movie = MovieFactory()

        response = client.get(seat_map_url(movie.id, 99999))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []
