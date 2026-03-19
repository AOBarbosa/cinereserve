from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import LoginSerializer, RegisterSerializer, UserSerializer


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    jwt_settings = settings.SIMPLE_JWT
    response.set_cookie(
        key=jwt_settings["AUTH_COOKIE_ACCESS"],
        value=access_token,
        max_age=int(jwt_settings["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=jwt_settings["AUTH_COOKIE_HTTP_ONLY"],
        secure=jwt_settings["AUTH_COOKIE_SECURE"],
        samesite=jwt_settings["AUTH_COOKIE_SAMESITE"],
    )
    response.set_cookie(
        key=jwt_settings["AUTH_COOKIE_REFRESH"],
        value=refresh_token,
        max_age=int(jwt_settings["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=jwt_settings["AUTH_COOKIE_HTTP_ONLY"],
        secure=jwt_settings["AUTH_COOKIE_SECURE"],
        samesite=jwt_settings["AUTH_COOKIE_SAMESITE"],
    )


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer}, tags=["Users"])
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=LoginSerializer, responses={200: UserSerializer}, tags=["Users"])
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = Response(UserSerializer(data["user"]).data, status=status.HTTP_200_OK)
        _set_auth_cookies(response, data["access"], data["refresh"])
        return response


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses={205: None}, tags=["Users"])
    def post(self, request: Request) -> Response:
        refresh_cookie = settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]
        refresh_token = request.COOKIES.get(refresh_cookie)
        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response({"detail": "Token is invalid or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)
        response = Response(status=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_ACCESS"])
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=None, responses={200: None}, tags=["Users"])
    def post(self, request: Request) -> Response:
        refresh_cookie = settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]
        refresh_token = request.COOKIES.get(refresh_cookie)
        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response(status=status.HTTP_200_OK)
        new_refresh = serializer.validated_data.get("refresh", refresh_token)
        _set_auth_cookies(response, serializer.validated_data["access"], new_refresh)
        return response
