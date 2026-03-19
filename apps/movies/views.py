from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request

from apps.movies.models import Movie
from apps.movies.serializers import MovieSerializer


def _is_admin(request: Request) -> bool:
    return request.user and request.user.is_authenticated and request.user.is_staff


class MovieListView(ListCreateAPIView):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()

    def get_queryset(self):
        if _is_admin(self.request):
            return Movie.objects.all()
        return Movie.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return [AllowAny()]

    @extend_schema(summary="List all movies")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create a movie (admin only)")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MovieDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()

    def get_queryset(self):
        if _is_admin(self.request):
            return Movie.objects.all()
        return Movie.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    @extend_schema(summary="Retrieve a movie")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Update a movie (admin only)")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update a movie or soft delete via is_active=False (admin only)"
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="Permanently delete a movie (admin only)")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
