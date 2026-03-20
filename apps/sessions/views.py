from datetime import timedelta

from django.core.cache import cache
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sessions.models import RESERVATION_TTL_MINUTES, MovieSession, Reservation, Seat
from apps.sessions.serializers import MovieSessionSerializer, ReservationSerializer, SeatSerializer


@extend_schema_view(
    get=extend_schema(summary="List active sessions for a movie", tags=["Sessions"]),
)
class MovieSessionListView(ListAPIView):
    serializer_class = MovieSessionSerializer
    queryset = MovieSession.objects.all()

    def get_queryset(self) -> QuerySet[MovieSession]:
        return MovieSession.objects.filter(
            movie_id=self.kwargs["movie_id"],
            is_active=True,
        )

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request: Request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(summary="List seats for a session", tags=["Seats"]),
)
class SeatMapView(ListAPIView):
    serializer_class = SeatSerializer
    permission_classes = (AllowAny,)
    queryset = Seat.objects.all()
    pagination_class = None

    def get_queryset(self):  # type: ignore[override]
        session_id = self.kwargs["session_id"]
        now = timezone.now()

        expired = Reservation.objects.filter(
            seat__session_id=session_id,
            expires_at__lt=now,
            is_confirmed=False,
        )
        if expired.exists():
            Seat.objects.filter(reservation__in=expired).update(status=Seat.Status.AVAILABLE)
            expired.delete()

        return Seat.objects.filter(session_id=session_id)


class ReserveSeatView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses={200: ReservationSerializer},
        summary="Reserve a seat",
        tags=["Seats"],
    )
    def post(self, request: Request, **kwargs) -> Response:
        seat = get_object_or_404(
            Seat,
            id=self.kwargs["seat_id"],
            session_id=self.kwargs["session_id"],
        )

        if seat.status != Seat.Status.AVAILABLE:
            return Response(
                {"detail": "Seat is not available."},
                status=status.HTTP_409_CONFLICT,
            )

        lock_key = f"seat_lock:{seat.id}"
        acquired = cache.add(lock_key, request.user.pk, timeout=RESERVATION_TTL_MINUTES * 60)
        if not acquired:
            return Response(
                {"detail": "Seat is currently being reserved."},
                status=status.HTTP_409_CONFLICT,
            )

        seat.refresh_from_db()
        if seat.status != Seat.Status.AVAILABLE:
            cache.delete(lock_key)
            return Response(
                {"detail": "Seat is not available."},
                status=status.HTTP_409_CONFLICT,
            )

        seat.status = Seat.Status.RESERVED
        seat.save()
        reservation = Reservation.objects.create(
            user=request.user,
            seat=seat,
            expires_at=timezone.now() + timedelta(minutes=RESERVATION_TTL_MINUTES),
        )
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_200_OK)


class ConfirmSeatView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses={200: ReservationSerializer},
        summary="Confirm a seat reservation",
        tags=["Seats"],
    )
    def post(self, request: Request, **kwargs) -> Response:
        reservation = get_object_or_404(
            Reservation,
            seat_id=self.kwargs["seat_id"],
            seat__session_id=self.kwargs["session_id"],
            user=request.user,
            is_confirmed=False,
        )

        if reservation.expires_at < timezone.now():
            reservation.seat.status = Seat.Status.AVAILABLE
            reservation.seat.save()
            reservation.delete()
            cache.delete(f"seat_lock:{reservation.seat_id}")
            return Response(
                {"detail": "Reservation has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.seat.status = Seat.Status.PURCHASED
        reservation.seat.save()
        reservation.is_confirmed = True
        reservation.save()
        cache.delete(f"seat_lock:{reservation.seat_id}")
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_200_OK)
