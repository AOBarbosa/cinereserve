from rest_framework import serializers

from apps.sessions.models import MovieSession, Seat


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "room", "start_time", "end_time", "price", "is_active")


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ("id", "row", "column", "status")
