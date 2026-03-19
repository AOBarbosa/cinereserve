from django.db import models

from apps.movies.models import Movie


class MovieSession(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="sessions")
    room = models.CharField(max_length=50)
    rows = models.PositiveIntegerField()
    columns = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self) -> str:
        return f"{self.movie.title} — {self.room} @ {self.start_time}"


class Seat(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        PURCHASED = "PURCHASED", "Purchased"

    session = models.ForeignKey(MovieSession, on_delete=models.CASCADE, related_name="seats")
    row = models.CharField(max_length=5)
    column = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        unique_together = ("session", "row", "column")

    def __str__(self) -> str:
        return f"{self.session} — {self.row}{self.column} ({self.status})"
