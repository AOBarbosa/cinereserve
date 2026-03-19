import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory

PASSWORD = "StrongPass123!"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_list_url():
    return reverse("user-list")


@pytest.fixture
def auth_client():
    client = APIClient()
    user = UserFactory()
    user.set_password(PASSWORD)
    user.save()
    client.post(
        reverse("user-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    return client


@pytest.fixture
def admin_client():
    client = APIClient()
    user = UserFactory(is_staff=True)
    user.set_password(PASSWORD)
    user.save()
    client.post(
        reverse("user-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    return client


@pytest.mark.django_db
class TestUserList:
    def test_unauthenticated_user_gets_401(self, client, user_list_url):
        response = client.get(user_list_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_regular_user_gets_403(self, auth_client, user_list_url):
        response = auth_client.get(user_list_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list_users(self, admin_client, user_list_url):
        response = admin_client.get(user_list_url)

        assert response.status_code == status.HTTP_200_OK

    def test_response_is_paginated(self, admin_client, user_list_url):
        response = admin_client.get(user_list_url)

        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    def test_returns_all_users(self, admin_client, user_list_url):
        UserFactory.create_batch(3)

        response = admin_client.get(user_list_url)

        assert response.data["count"] == 4

    def test_response_contains_expected_fields(self, admin_client, user_list_url):
        response = admin_client.get(user_list_url)

        user = response.data["results"][0]
        assert "id" in user
        assert "email" in user
        assert "username" in user
        assert "created_at" in user

    def test_sensitive_fields_not_exposed(self, admin_client, user_list_url):
        response = admin_client.get(user_list_url)

        user = response.data["results"][0]
        assert "password" not in user
        assert "is_staff" not in user
        assert "is_superuser" not in user

    def test_users_ordered_by_created_at_desc(self, admin_client, user_list_url):
        UserFactory.create_batch(3)

        response = admin_client.get(user_list_url)

        created_ats = [u["created_at"] for u in response.data["results"]]
        assert created_ats == sorted(created_ats, reverse=True)

    def test_pagination_page_size(self, admin_client, user_list_url):
        UserFactory.create_batch(25)

        response = admin_client.get(user_list_url)

        assert len(response.data["results"]) == 20
        assert response.data["next"] is not None

    def test_pagination_second_page(self, admin_client, user_list_url):
        UserFactory.create_batch(25)

        response = admin_client.get(user_list_url, {"page": 2})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 6
