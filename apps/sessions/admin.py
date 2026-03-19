from django.contrib import admin

from apps.sessions.models import MovieSession, Seat


@admin.register(MovieSession)
class MovieSessionAdmin(admin.ModelAdmin):
    list_display = ("movie", "room", "start_time", "end_time", "price", "is_active")
    list_filter = ("is_active", "movie")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("session", "row", "column", "status")
    list_filter = ("status",)
