import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.users.tests.factories import UserFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def register_url():
    return reverse("user-register")


@pytest.fixture
def valid_payload():
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
    }


@pytest.mark.django_db
class TestRegisterView:
    def test_register_success(self, client, register_url, valid_payload):
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == valid_payload["email"]
        assert response.data["username"] == valid_payload["username"]
        assert "id" in response.data
        assert "password" not in response.data

    def test_register_creates_user_in_db(self, client, register_url, valid_payload):
        client.post(register_url, valid_payload, format="json")

        assert User.objects.filter(email=valid_payload["email"]).exists()

    def test_register_passwords_do_not_match(self, client, register_url, valid_payload):
        valid_payload["password_confirm"] = "DifferentPass456!"
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_register_duplicate_email(self, client, register_url, valid_payload):
        UserFactory(email=valid_payload["email"])
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_duplicate_username(self, client, register_url, valid_payload):
        UserFactory(username=valid_payload["username"])
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_register_missing_email(self, client, register_url, valid_payload):
        del valid_payload["email"]
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_missing_username(self, client, register_url, valid_payload):
        del valid_payload["username"]
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_register_missing_password(self, client, register_url, valid_payload):
        del valid_payload["password"]
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_register_invalid_email_format(self, client, register_url, valid_payload):
        valid_payload["email"] = "not-an-email"
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_weak_password(self, client, register_url, valid_payload):
        valid_payload["password"] = "123"
        valid_payload["password_confirm"] = "123"
        response = client.post(register_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data
