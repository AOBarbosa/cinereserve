import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"
ACCESS_COOKIE = settings.SIMPLE_JWT["AUTH_COOKIE_ACCESS"]
REFRESH_COOKIE = settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]


@pytest.fixture
def client():
    return APIClient(enforce_csrf_checks=False)


@pytest.fixture
def login_url():
    return reverse("user-login")


@pytest.fixture
def logout_url():
    return reverse("user-logout")


@pytest.fixture
def token_refresh_url():
    return reverse("token_refresh")


@pytest.fixture
def active_user():
    user = UserFactory()
    user.set_password(PASSWORD)
    user.save()
    return user


@pytest.fixture
def auth_client(client, active_user, login_url):
    client.post(login_url, {"email": active_user.email, "password": PASSWORD}, format="json")
    return client


@pytest.mark.django_db
class TestLogin:
    def test_login_success_sets_cookies(self, client, login_url, active_user):
        response = client.post(login_url, {"email": active_user.email, "password": PASSWORD}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert ACCESS_COOKIE in response.cookies
        assert REFRESH_COOKIE in response.cookies

    def test_login_success_returns_user_data(self, client, login_url, active_user):
        response = client.post(login_url, {"email": active_user.email, "password": PASSWORD}, format="json")

        assert response.data["email"] == active_user.email
        assert response.data["username"] == active_user.username
        assert "password" not in response.data

    def test_login_cookies_are_httponly(self, client, login_url, active_user):
        response = client.post(login_url, {"email": active_user.email, "password": PASSWORD}, format="json")

        assert response.cookies[ACCESS_COOKIE]["httponly"]
        assert response.cookies[REFRESH_COOKIE]["httponly"]

    def test_login_wrong_password(self, client, login_url, active_user):
        response = client.post(login_url, {"email": active_user.email, "password": "WrongPass!"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert ACCESS_COOKIE not in response.cookies

    def test_login_nonexistent_user(self, client, login_url):
        response = client.post(login_url, {"email": "ghost@example.com", "password": PASSWORD}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_email(self, client, login_url):
        response = client.post(login_url, {"password": PASSWORD}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_login_missing_password(self, client, login_url):
        response = client.post(login_url, {"email": "x@example.com"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_inactive_user_cannot_login(self, client, login_url, active_user):
        active_user.is_active = False
        active_user.save()

        response = client.post(login_url, {"email": active_user.email, "password": PASSWORD}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCookieAuth:
    def test_cookie_authorizes_protected_endpoint(self, auth_client):
        response = auth_client.get(reverse("schema"))

        assert response.status_code == status.HTTP_200_OK

    def test_request_without_cookie_is_unauthorized(self, client, logout_url):
        response = client.post(logout_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_sets_new_cookies(self, auth_client, token_refresh_url):
        response = auth_client.post(token_refresh_url)

        assert response.status_code == status.HTTP_200_OK
        assert ACCESS_COOKIE in response.cookies
        assert REFRESH_COOKIE in response.cookies

    def test_refresh_without_cookie_returns_400(self, client, token_refresh_url):
        response = client.post(token_refresh_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_new_access_cookie_authorizes_requests(self, auth_client, token_refresh_url):
        auth_client.post(token_refresh_url)

        response = auth_client.get(reverse("schema"))

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestLogout:
    def test_logout_success(self, auth_client, logout_url):
        response = auth_client.post(logout_url)

        assert response.status_code == status.HTTP_205_RESET_CONTENT

    def test_logout_clears_cookies(self, auth_client, logout_url):
        response = auth_client.post(logout_url)

        assert response.cookies[ACCESS_COOKIE].value == ""
        assert response.cookies[REFRESH_COOKIE].value == ""

    def test_logout_requires_authentication(self, client, logout_url):
        response = client.post(logout_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_blacklists_refresh_token(self, auth_client, logout_url, token_refresh_url):
        auth_client.post(logout_url)

        response = auth_client.post(token_refresh_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_already_blacklisted_token(self, auth_client, logout_url):
        auth_client.post(logout_url)
        response = auth_client.post(logout_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
