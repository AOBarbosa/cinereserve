from django.urls import path

from apps.sessions.views import ConfirmSeatView, MovieSessionListView, ReserveSeatView, SeatMapView

urlpatterns = [
    path("", MovieSessionListView.as_view(), name="movie-session-list"),
    path("<int:session_id>/seats/", SeatMapView.as_view(), name="seat-map"),
    path("<int:session_id>/seats/<int:seat_id>/reserve/", ReserveSeatView.as_view(), name="seat-reserve"),
    path("<int:session_id>/seats/<int:seat_id>/confirm/", ConfirmSeatView.as_view(), name="seat-confirm"),
]
