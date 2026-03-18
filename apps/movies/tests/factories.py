import factory

from apps.movies.models import Movie


class MovieFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Movie
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f"Movie {n}")
    description = factory.Faker("paragraph")
    release_year = factory.Faker("year")
    duration = factory.Faker("random_int", min=60, max=180)
    genre = factory.Faker("word")
    director = factory.Faker("name")
    rating = factory.Faker("pydecimal", left_digits=1, right_digits=1, positive=True, max_value=9)
