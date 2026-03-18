import pytest

from apps.users.models import User
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_success(self):
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
        )

        assert user.pk is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password("StrongPass123!") is True

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM",
            username="testuser",
            password="StrongPass123!",
        )

        assert user.email == "Test@example.com"

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="Email is required."):
            User.objects.create_user(email="", username="testuser", password="pass")

    def test_create_user_requires_username(self):
        with pytest.raises(ValueError, match="Username is required."):
            User.objects.create_user(email="test@example.com", username="", password="pass")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="StrongPass123!",
        )

        assert user.is_staff is True
        assert user.is_superuser is True

    def test_email_is_unique(self):
        from django.db import IntegrityError

        User.objects.create_user(email="dup@example.com", username="user1", password="Pass123!")
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="dup@example.com", username="user2", password="Pass123!")

    def test_username_is_unique(self):
        from django.db import IntegrityError

        UserFactory(username="duplicated")
        with pytest.raises(IntegrityError):
            UserFactory(username="duplicated")

    def test_str_returns_email(self):
        user = UserFactory(email="str@example.com")
        assert str(user) == "str@example.com"
