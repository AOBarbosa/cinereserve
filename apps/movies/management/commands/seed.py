import string
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.movies.models import Movie
from apps.sessions.models import MovieSession, Reservation, Seat
from apps.users.models import User


class Command(BaseCommand):
    help = "Seed the database with default users, movies, sessions, and reservations."

    def handle(self, *args, **kwargs) -> None:
        self._create_users()
        movies = self._create_movies()
        sessions = self._create_sessions(movies)
        self._create_reservations(sessions)
        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))

    def _create_users(self) -> None:
        _, created = User.objects.get_or_create(
            email="user@cinereserve.com",
            defaults={"username": "default_user", "is_staff": False},
        )
        if created:
            user = User.objects.get(email="user@cinereserve.com")
            user.set_password("User@1234!")
            user.save()
            self.stdout.write("  Created user: user@cinereserve.com")
        else:
            self.stdout.write("  Skipped user@cinereserve.com (already exists)")

        _, created = User.objects.get_or_create(
            email="admin@cinereserve.com",
            defaults={"username": "admin", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin = User.objects.get(email="admin@cinereserve.com")
            admin.set_password("Admin@1234!")
            admin.save()
            self.stdout.write("  Created admin: admin@cinereserve.com")
        else:
            self.stdout.write("  Skipped admin@cinereserve.com (already exists)")

    def _create_movies(self) -> list[Movie]:
        movies_data = [
            {
                "title": "The Dark Knight",
                "description": "Batman faces the Joker, a criminal mastermind who plunges Gotham into chaos.",
                "release_year": 2008,
                "duration": 152,
                "genre": "Action",
                "director": "Christopher Nolan",
                "rating": "9.0",
            },
            {
                "title": "Inception",
                "description": "A thief who steals corporate secrets through dream-sharing technology.",
                "release_year": 2010,
                "duration": 148,
                "genre": "Sci-Fi",
                "director": "Christopher Nolan",
                "rating": "8.8",
            },
        ]

        movies = []
        for data in movies_data:
            movie, created = Movie.objects.get_or_create(
                title=data["title"],
                defaults=data,
            )
            status = "Created" if created else "Skipped"
            self.stdout.write(f"  {status} movie: {movie.title}")
            movies.append(movie)

        return movies

    def _create_sessions(self, movies: list[Movie]) -> list[MovieSession]:
        now = timezone.now().replace(minute=0, second=0, microsecond=0)

        sessions_data = [
            # Past sessions (for purchase history)
            {"room": "Room E", "offset_hours": -48, "rows": 10, "columns": 15},
            {"room": "Room F", "offset_hours": -24, "rows": 8, "columns": 12},
            # Future sessions (upcoming)
            {"room": "Room A", "offset_hours": 2, "rows": 10, "columns": 15},
            {"room": "Room B", "offset_hours": 5, "rows": 8, "columns": 12},
            {"room": "Room C", "offset_hours": 24, "rows": 12, "columns": 20},
            {"room": "Room D", "offset_hours": 27, "rows": 6, "columns": 10},
        ]

        all_sessions = []
        for movie in movies:
            for data in sessions_data:
                start_time = now + timedelta(hours=data["offset_hours"])
                end_time = start_time + timedelta(minutes=movie.duration)

                session, created = MovieSession.objects.get_or_create(
                    movie=movie,
                    room=data["room"],
                    defaults={
                        "start_time": start_time,
                        "end_time": end_time,
                        "rows": data["rows"],
                        "columns": data["columns"],
                        "price": 0,
                        "is_active": True,
                    },
                )
                if not created and not session.seats.exists():
                    seats = [
                        Seat(session=session, row=string.ascii_uppercase[r], column=c)
                        for r in range(session.rows)
                        for c in range(1, session.columns + 1)
                    ]
                    Seat.objects.bulk_create(seats)
                    created = True  # treat as freshly seeded for the label

                label = "Created" if created else "Skipped"
                self.stdout.write(
                    f"  {label} session: {movie.title} @ {data['room']} — {start_time:%Y-%m-%d %H:%M}"
                )
                all_sessions.append(session)

        return all_sessions

    def _create_reservations(self, sessions: list[MovieSession]) -> None:
        user = User.objects.get(email="user@cinereserve.com")
        now = timezone.now()

        # sessions list order: [movie0_room_e, movie0_room_f, movie0_room_a, movie0_room_b, ...]
        # Index 0 → The Dark Knight / Room E (past)
        # Index 2 → The Dark Knight / Room A (future, +2h)
        # Index 3 → The Dark Knight / Room B (future, +5h)

        past_session = sessions[0]  # Room E, past
        future_session_a = sessions[2]  # Room A, future
        future_session_b = sessions[3]  # Room B, future

        # 1. Confirmed ticket in a past session (purchase history)
        past_seat = past_session.seats.order_by("row", "column").first()
        if past_seat and not Reservation.objects.filter(seat=past_seat).exists():
            past_seat.status = Seat.Status.PURCHASED
            past_seat.save()
            Reservation.objects.create(
                user=user,
                seat=past_seat,
                expires_at=past_session.start_time + timedelta(minutes=10),
                is_confirmed=True,
            )
            self.stdout.write(
                f"  Created confirmed ticket (past): {past_session.movie.title} @ {past_session.room} — seat {past_seat.row}{past_seat.column}"  # noqa: E501
            )
        else:
            self.stdout.write("  Skipped past ticket (already exists)")

        # 2. Confirmed ticket in a future session (upcoming)
        future_seat_a = future_session_a.seats.order_by("row", "column").first()
        if (
            future_seat_a
            and not Reservation.objects.filter(seat=future_seat_a).exists()
        ):
            future_seat_a.status = Seat.Status.PURCHASED
            future_seat_a.save()
            Reservation.objects.create(
                user=user,
                seat=future_seat_a,
                expires_at=now + timedelta(minutes=10),
                is_confirmed=True,
            )
            self.stdout.write(
                f"  Created confirmed ticket (upcoming): {future_session_a.movie.title} @ {future_session_a.room} — seat {future_seat_a.row}{future_seat_a.column}"  # noqa: E501
            )
        else:
            self.stdout.write("  Skipped upcoming ticket (already exists)")

        # 3. Pending reservation in a future session (RESERVED, awaiting confirm/)
        future_seat_b = future_session_b.seats.order_by("row", "column").first()
        if (
            future_seat_b
            and not Reservation.objects.filter(seat=future_seat_b).exists()
        ):
            future_seat_b.status = Seat.Status.RESERVED
            future_seat_b.save()
            Reservation.objects.create(
                user=user,
                seat=future_seat_b,
                expires_at=now + timedelta(minutes=10),
                is_confirmed=False,
            )
            self.stdout.write(
                f"  Created pending reservation: {future_session_b.movie.title} @ {future_session_b.room} — seat {future_seat_b.row}{future_seat_b.column}"  # noqa: E501
            )
        else:
            self.stdout.write("  Skipped pending reservation (already exists)")

        # 4. Extra occupied seats in Room A (for seat map variety)
        #    A2, A3, B1, B2 → PURCHASED  |  C1, C2 → RESERVED
        admin = User.objects.get(email="admin@cinereserve.com")
        occupied = [
            ("A", 2, Seat.Status.PURCHASED, True),
            ("A", 3, Seat.Status.PURCHASED, True),
            ("B", 1, Seat.Status.PURCHASED, True),
            ("B", 2, Seat.Status.PURCHASED, True),
            ("C", 1, Seat.Status.RESERVED, False),
            ("C", 2, Seat.Status.RESERVED, False),
        ]
        for row, col, seat_status, is_confirmed in occupied:
            seat = future_session_a.seats.filter(row=row, column=col).first()
            if seat and not Reservation.objects.filter(seat=seat).exists():
                seat.status = seat_status
                seat.save()
                Reservation.objects.create(
                    user=admin,
                    seat=seat,
                    expires_at=now + timedelta(minutes=10),
                    is_confirmed=is_confirmed,
                )
                self.stdout.write(
                    f"  Occupied seat {row}{col} ({seat_status}) in {future_session_a.room}"
                )
            else:
                self.stdout.write(
                    f"  Skipped seat {row}{col} in {future_session_a.room} (already exists)"
                )
