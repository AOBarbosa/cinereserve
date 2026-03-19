import factory
from datetime import timedelta
from factory.declarations import Sequence, SubFactory
from django.utils import timezone

from apps.movies.tests.factories import MovieFactory
from apps.sessions.models import MovieSession, Seat


class MovieSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MovieSession
        skip_postgeneration_save = True

    movie = SubFactory(MovieFactory)
    room = Sequence(lambda n: f"Room {chr(65 + n % 26)}")
    rows = 5
    columns = 10
    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=3))
    price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True, max_value=50)
    is_active = True


class SeatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Seat
        skip_postgeneration_save = True

    session = SubFactory(MovieSessionFactory)
    row = "A"
    column = Sequence(lambda n: n + 1)
    status = Seat.Status.AVAILABLE
