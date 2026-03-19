from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request

from apps.sessions.models import MovieSession
from apps.sessions.serializers import MovieSessionSerializer


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
