import pytest
from django.db import IntegrityError

from apps.sessions.models import Seat
from apps.sessions.tests.factories import MovieSessionFactory


@pytest.mark.django_db
class TestSeatGeneration:
    def test_creating_session_generates_seats(self):
        session = MovieSessionFactory(rows=3, columns=4)

        assert session.seats.count() == 12  # 3 × 4

    def test_seat_count_matches_rows_times_columns(self):
        session = MovieSessionFactory(rows=5, columns=10)

        assert session.seats.count() == 50

    def test_row_labels_are_uppercase_letters(self):
        session = MovieSessionFactory(rows=3, columns=1)

        rows = list(session.seats.values_list("row", flat=True).order_by("row"))

        assert rows == ["A", "B", "C"]

    def test_column_numbers_start_at_one(self):
        session = MovieSessionFactory(rows=1, columns=4)

        columns = sorted(session.seats.values_list("column", flat=True))

        assert columns == [1, 2, 3, 4]

    def test_all_generated_seats_are_available(self):
        session = MovieSessionFactory(rows=2, columns=3)

        statuses = session.seats.values_list("status", flat=True)

        assert all(s == Seat.Status.AVAILABLE for s in statuses)

    def test_all_seats_belong_to_the_session(self):
        session = MovieSessionFactory(rows=2, columns=2)

        session_ids = session.seats.values_list("session_id", flat=True).distinct()

        assert list(session_ids) == [session.id]

    def test_updating_session_does_not_generate_new_seats(self):
        session = MovieSessionFactory(rows=2, columns=2)

        session.room = "Updated Room"
        session.save()

        assert session.seats.count() == 4  # unchanged

    def test_seat_row_column_combination_is_unique(self):
        session = MovieSessionFactory(rows=1, columns=1)

        with pytest.raises(IntegrityError):
            Seat.objects.create(session=session, row="A", column=1)

    def test_different_sessions_have_independent_seats(self):
        session_a = MovieSessionFactory(rows=2, columns=2)
        session_b = MovieSessionFactory(rows=3, columns=3)

        assert session_a.seats.count() == 4
        assert session_b.seats.count() == 9
