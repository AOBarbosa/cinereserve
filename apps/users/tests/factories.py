import factory
from factory.declarations import PostGenerationMethodCall, Sequence

from apps.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:  # type: ignore[override]
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = Sequence(lambda n: f"user{n}@example.com")
    username = Sequence(lambda n: f"user{n}")
    password = PostGenerationMethodCall("set_password", "StrongPass123!")
    is_active = True
    is_staff = False
