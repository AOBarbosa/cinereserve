from rest_framework import serializers

from apps.sessions.models import MovieSession, Reservation, Seat


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "room", "start_time", "end_time", "price", "is_active")


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ("id", "row", "column", "status")


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ("id", "seat", "expires_at", "is_confirmed", "created_at")
        read_only_fields = ("id", "expires_at", "is_confirmed", "created_at")
