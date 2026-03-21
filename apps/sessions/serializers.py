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
        fields = ("id", "seat", "ticket_code", "expires_at", "is_confirmed", "created_at")
        read_only_fields = ("id", "ticket_code", "expires_at", "is_confirmed", "created_at")


class TicketSerializer(serializers.ModelSerializer):
    seat_row = serializers.CharField(source="seat.row")
    seat_column = serializers.IntegerField(source="seat.column")
    session_room = serializers.CharField(source="seat.session.room")
    session_start_time = serializers.DateTimeField(source="seat.session.start_time")
    session_end_time = serializers.DateTimeField(source="seat.session.end_time")
    movie_title = serializers.CharField(source="seat.session.movie.title")

    class Meta:
        model = Reservation
        fields = (
            "id",
            "ticket_code",
            "movie_title",
            "session_room",
            "session_start_time",
            "session_end_time",
            "seat_row",
            "seat_column",
            "created_at",
        )
        read_only_fields = fields
