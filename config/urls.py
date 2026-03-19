from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenVerifyView


class TaggedTokenVerifyView(TokenVerifyView):
    @extend_schema(tags=["Users"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


api_v1_patterns = [
    path("auth/token/verify/", TaggedTokenVerifyView.as_view(), name="token_verify"),
    path("users/", include("apps.users.urls")),
    path("movies/", include("apps.movies.urls")),
    path("movies/<int:movie_id>/sessions/", include("apps.sessions.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
