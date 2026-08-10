import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from events.models import Event

User = get_user_model()


@pytest.fixture
def organizer(db):
    return User.objects.create_user(
        email="organizador@example.com",
        first_name="Rafael",
        last_name="Casemiro",
        password="senha123",
        role=User.Role.ORGANIZADOR,
    )


@pytest.mark.django_db
class TestEventModel:
    def test_creates_published_event_for_organizer(self, organizer):
        event = Event.objects.create(
            title="Duna: Parte Dois",
            description="Filme de ficção científica",
            date=timezone.now(),
            location="Cine Verzel",
            capacity=100,
            price="35.00",
            organizer=organizer,
            external_ref=693134,
            external_title="Dune: Part Two",
            is_published=True,
        )
        assert event.pk is not None
        assert event.organizer == organizer

    def test_event_defaults_to_unpublished(self, organizer):
        event = Event.objects.create(
            title="Rascunho",
            date=timezone.now(),
            location="Cine Verzel",
            capacity=50,
            price="20.00",
            organizer=organizer,
            external_ref=1,
        )
        assert event.is_published is False

    def test_string_representation_is_the_title(self, organizer):
        event = Event.objects.create(
            title="Oppenheimer",
            date=timezone.now(),
            location="Cine Verzel",
            capacity=80,
            price="30.00",
            organizer=organizer,
            external_ref=872585,
        )
        assert str(event) == "Oppenheimer"

    def test_deleting_organizer_deletes_their_events(self, organizer):
        Event.objects.create(
            title="Evento do organizador",
            date=timezone.now(),
            location="Cine Verzel",
            capacity=10,
            price="10.00",
            organizer=organizer,
            external_ref=2,
        )
        organizer.delete()
        assert Event.objects.count() == 0
