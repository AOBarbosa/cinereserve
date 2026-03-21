import string
import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.movies.models import Movie

RESERVATION_TTL_MINUTES = 10


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

    session = models.ForeignKey(
        MovieSession, on_delete=models.CASCADE, related_name="seats"
    )
    row = models.CharField(max_length=5)
    column = models.PositiveIntegerField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.AVAILABLE
    )

    class Meta:
        unique_together = ("session", "row", "column")

    def __str__(self) -> str:
        return f"{self.session} — {self.row}{self.column} ({self.status})"


class Reservation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    seat = models.OneToOneField(
        Seat, on_delete=models.CASCADE, related_name="reservation"
    )
    ticket_code = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Reservation {self.id} — {self.user} → {self.seat}"


@receiver(post_save, sender=MovieSession)
def create_seats_for_session(sender, instance, created, **kwargs):
    if not created:
        return
    seats = [
        Seat(session=instance, row=string.ascii_uppercase[row_idx], column=col)
        for row_idx in range(instance.rows)
        for col in range(1, instance.columns + 1)
    ]
    Seat.objects.bulk_create(seats)
