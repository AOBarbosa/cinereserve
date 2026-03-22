from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request

from apps.movies.models import Movie
from apps.movies.serializers import MovieSerializer


def _is_admin(request: Request) -> bool:
    return request.user and request.user.is_authenticated and request.user.is_staff


@extend_schema_view(
    get=extend_schema(summary="List all movies", tags=["Movies"]),
    post=extend_schema(summary="Create a movie (admin only)", tags=["Movies"]),
)
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

    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(summary="Retrieve a movie", tags=["Movies"]),
    put=extend_schema(summary="Update a movie (admin only)", tags=["Movies"]),
    patch=extend_schema(
        summary="Partially update a movie or soft delete via is_active=False (admin only)",
        tags=["Movies"],
    ),
    delete=extend_schema(summary="Permanently delete a movie (admin only)", tags=["Movies"]),
)
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

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
