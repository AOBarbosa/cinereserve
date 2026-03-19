from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.movies.models import Movie
from apps.sessions.models import MovieSession
from apps.users.models import User


class Command(BaseCommand):
    help = "Seed the database with default users, movies, and sessions."

    def handle(self, *args, **kwargs) -> None:
        self._create_users()
        movies = self._create_movies()
        self._create_sessions(movies)
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

    def _create_sessions(self, movies: list[Movie]) -> None:
        now = timezone.now().replace(minute=0, second=0, microsecond=0)

        sessions_data = [
            {"room": "Room A", "offset_hours": 2,  "rows": 10, "columns": 15},
            {"room": "Room B", "offset_hours": 5,  "rows": 8,  "columns": 12},
            {"room": "Room C", "offset_hours": 24, "rows": 12, "columns": 20},
            {"room": "Room D", "offset_hours": 27, "rows": 6,  "columns": 10},
        ]

        for movie in movies:
            for data in sessions_data:
                start_time = now + timedelta(hours=data["offset_hours"])
                end_time = start_time + timedelta(minutes=movie.duration)

                session, created = MovieSession.objects.get_or_create(
                    movie=movie,
                    room=data["room"],
                    start_time=start_time,
                    defaults={
                        "end_time": end_time,
                        "rows": data["rows"],
                        "columns": data["columns"],
                        "price": 0,
                        "is_active": True,
                    },
                )
                status = "Created" if created else "Skipped"
                self.stdout.write(f"  {status} session: {movie.title} @ {data['room']} — {start_time:%Y-%m-%d %H:%M}")
