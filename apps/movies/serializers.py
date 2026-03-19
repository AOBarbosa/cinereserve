from rest_framework import serializers

from apps.movies.models import Movie


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "release_year",
            "duration",
            "genre",
            "director",
            "rating",
            "is_active",
        )
