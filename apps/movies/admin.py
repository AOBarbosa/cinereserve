from django.contrib import admin

from apps.movies.models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "director", "release_year", "rating", "is_active")
    list_filter = ("genre", "release_year", "is_active")
    search_fields = ("title", "director")
    ordering = ("-release_year",)
