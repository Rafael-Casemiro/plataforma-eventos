import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from events.models import Event

User = get_user_model()

EVENTS_LIST_URL = "/api/v1/events/"
EVENTS_MINE_URL = "/api/v1/events/mine/"
EVENTS_CREATE_URL = "/api/v1/events/create/"
AUTH_LOGIN_URL = "/api/v1/auth/login/"


@pytest.fixture
def organizer(db):
    return User.objects.create_user(
        email="organizador@example.com",
        first_name="Rafael",
        last_name="Casemiro",
        password="senha123",
        role=User.Role.ORGANIZADOR,
    )


@pytest.fixture
def another_organizer(db):
    return User.objects.create_user(
        email="outro.organizador@example.com",
        first_name="Marina",
        last_name="Souza",
        password="senha123",
        role=User.Role.ORGANIZADOR,
    )


@pytest.fixture
def cliente(db):
    return User.objects.create_user(
        email="cliente@example.com",
        first_name="Ana",
        last_name="Silva",
        password="senha123",
        role=User.Role.CLIENTE,
    )


@pytest.fixture
def published_event(organizer):
    return Event.objects.create(
        title="Oppenheimer",
        description="Filme biográfico",
        date=timezone.now(),
        location="Cine Verzel",
        capacity=80,
        price="30.00",
        organizer=organizer,
        external_ref=872585,
        is_published=True,
    )


@pytest.fixture
def api_client():
    return APIClient()


def _login(api_client, user, password="senha123"):
    return api_client.post(
        AUTH_LOGIN_URL, {"email": user.email, "password": password}, format="json"
    )


def _event_payload(**overrides):
    payload = {
        "title": "Duna: Parte Dois",
        "description": "Filme de ficção científica",
        "date": "2026-09-20T20:00:00Z",
        "location": "Cine Verzel",
        "capacity": 100,
        "price": "35.00",
        "external_ref": 693134,
        "external_title": "Dune: Part Two",
        "poster_path": "",
        "is_published": True,
    }
    payload.update(overrides)
    return payload


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


@pytest.mark.django_db
class TestPublicEventListing:
    def test_lists_only_published_events(self, api_client, organizer):
        Event.objects.create(
            title="Publicado", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=1,
            is_published=True,
        )
        Event.objects.create(
            title="Rascunho", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=2,
            is_published=False,
        )

        response = api_client.get(EVENTS_LIST_URL)

        titles = [evento["title"] for evento in response.data["eventos"]]
        assert titles == ["Publicado"]

    def test_does_not_require_authentication(self, api_client, published_event):
        response = api_client.get(EVENTS_LIST_URL)
        assert response.status_code == 200

    def test_filters_by_search_text(self, api_client, organizer):
        Event.objects.create(
            title="Duna: Parte Dois", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=1,
            is_published=True,
        )
        Event.objects.create(
            title="Oppenheimer", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=2,
            is_published=True,
        )

        response = api_client.get(EVENTS_LIST_URL, {"search": "duna"})

        titles = [evento["title"] for evento in response.data["eventos"]]
        assert titles == ["Duna: Parte Dois"]

    def test_filters_by_exact_date(self, api_client, organizer):
        Event.objects.create(
            title="Sessão de hoje", date="2026-09-20T20:00:00Z", location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=1,
            is_published=True,
        )
        Event.objects.create(
            title="Sessão de amanhã", date="2026-09-21T20:00:00Z", location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=2,
            is_published=True,
        )

        response = api_client.get(EVENTS_LIST_URL, {"date": "2026-09-20"})

        titles = [evento["title"] for evento in response.data["eventos"]]
        assert titles == ["Sessão de hoje"]

    def test_filters_by_price_range(self, api_client, organizer):
        Event.objects.create(
            title="Barato", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=1,
            is_published=True,
        )
        Event.objects.create(
            title="Caro", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="90.00", organizer=organizer, external_ref=2,
            is_published=True,
        )

        response = api_client.get(EVENTS_LIST_URL, {"price_min": "50", "price_max": "100"})

        titles = [evento["title"] for evento in response.data["eventos"]]
        assert titles == ["Caro"]


@pytest.mark.django_db
class TestOrganizerEventListing:
    def test_returns_only_own_events_including_drafts(
        self, api_client, organizer, another_organizer
    ):
        Event.objects.create(
            title="Publicado do dono", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=1,
            is_published=True,
        )
        Event.objects.create(
            title="Rascunho do dono", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=organizer, external_ref=2,
            is_published=False,
        )
        Event.objects.create(
            title="Publicado de outro organizador", date=timezone.now(), location="Cine Verzel",
            capacity=10, price="10.00", organizer=another_organizer, external_ref=3,
            is_published=True,
        )

        _login(api_client, organizer)

        response = api_client.get(EVENTS_MINE_URL)

        titles = {evento["title"] for evento in response.data["eventos"]}
        assert titles == {"Publicado do dono", "Rascunho do dono"}

    def test_cliente_cannot_access(self, api_client, cliente):
        _login(api_client, cliente)
        response = api_client.get(EVENTS_MINE_URL)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access(self, api_client):
        response = api_client.get(EVENTS_MINE_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestCreateEventView:
    def test_organizador_can_create_event(self, api_client, organizer):
        _login(api_client, organizer)

        response = api_client.post(EVENTS_CREATE_URL, _event_payload(), format="json")

        assert response.status_code == 201
        assert response.data["organizer"] == organizer.id

    def test_cliente_cannot_create_event(self, api_client, cliente):
        _login(api_client, cliente)

        response = api_client.post(EVENTS_CREATE_URL, _event_payload(), format="json")

        assert response.status_code == 403

    def test_unauthenticated_cannot_create_event(self, api_client):
        response = api_client.post(EVENTS_CREATE_URL, _event_payload(), format="json")
        assert response.status_code == 401

    def test_organizer_field_cannot_be_overridden_by_payload(self, api_client, organizer, another_organizer):
        _login(api_client, organizer)

        response = api_client.post(
            EVENTS_CREATE_URL,
            _event_payload(organizer=another_organizer.id),
            format="json",
        )

        assert response.status_code == 201
        assert response.data["organizer"] == organizer.id


@pytest.mark.django_db
class TestUpdateEventView:
    def test_owner_can_replace_event_via_put(self, api_client, organizer, published_event):
        _login(api_client, organizer)

        response = api_client.put(
            f"/api/v1/events/{published_event.pk}/",
            _event_payload(title="Oppenheimer 2"),
            format="json",
        )

        assert response.status_code == 200
        assert response.data["title"] == "Oppenheimer 2"

    def test_owner_can_partially_update_via_patch(self, api_client, organizer, published_event):
        _login(api_client, organizer)

        response = api_client.patch(
            f"/api/v1/events/{published_event.pk}/",
            {"title": "Novo título"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["title"] == "Novo título"

    def test_non_owner_organizador_cannot_update(self, api_client, another_organizer, published_event):
        _login(api_client, another_organizer)

        response = api_client.patch(
            f"/api/v1/events/{published_event.pk}/",
            {"title": "Hackeado"},
            format="json",
        )

        assert response.status_code == 403

    def test_cliente_cannot_update(self, api_client, cliente, published_event):
        _login(api_client, cliente)

        response = api_client.patch(
            f"/api/v1/events/{published_event.pk}/",
            {"title": "Hackeado"},
            format="json",
        )

        assert response.status_code == 403

    def test_updating_nonexistent_event_returns_404(self, api_client, organizer):
        _login(api_client, organizer)

        response = api_client.patch(
            "/api/v1/events/999999/",
            {"title": "X"},
            format="json",
        )

        assert response.status_code == 404
