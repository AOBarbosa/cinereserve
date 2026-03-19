import factory
from factory.declarations import Sequence
from factory.faker import Faker

from apps.movies.models import Movie


class MovieFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Movie
        skip_postgeneration_save = True

    title = Sequence(lambda n: f"Movie {n}")
    description = Faker("paragraph")
    release_year = Faker("year")
    duration = Faker("random_int", min=60, max=180)
    genre = Faker("word")
    director = Faker("name")
    rating = Faker(
        "pydecimal", left_digits=1, right_digits=1, positive=True, max_value=9
    )
