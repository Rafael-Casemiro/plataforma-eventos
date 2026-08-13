import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
import concurrent.futures

from events.models import Event
from reservations.models import Payment, Reservation, Ticket

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organizer(db):
    return User.objects.create_user(
        email="organizador_res@example.com",
        first_name="Rafael",
        last_name="Casemiro",
        password="senha123",
        role=User.Role.ORGANIZADOR,
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        email="cliente_res@example.com",
        first_name="Joana",
        last_name="Souza",
        password="senha123",
    )


@pytest.fixture
def portaria(db):
    return User.objects.create_user(
        email="portaria_res@example.com",
        first_name="Diego",
        last_name="Alves",
        password="senha123",
        role=User.Role.PORTARIA,
    )


@pytest.fixture
def event(db, organizer):
    return Event.objects.create(
        title="Duna: Parte Dois",
        date=timezone.now() + timedelta(days=5),
        location="Cine Verzel",
        capacity=100,
        price="35.00",
        organizer=organizer,
        external_ref=693134,
        is_published=True,
    )


@pytest.mark.django_db
class TestReservationModel:
    def test_creates_pending_reservation_by_default(self, event, customer):
        reservation = Reservation.objects.create(customer=customer, event=event, quantity=2)
        assert reservation.status == Reservation.Status.PENDENTE

    def test_deleting_event_deletes_its_reservations(self, event, customer):
        Reservation.objects.create(customer=customer, event=event, quantity=1)
        event.delete()
        assert Reservation.objects.count() == 0


@pytest.mark.django_db
class TestTicketModel:
    def test_creates_ticket_linked_to_reservation_with_unique_tokens(self, event, customer):
        reservation = Reservation.objects.create(customer=customer, event=event, quantity=1)
        ticket = Ticket.objects.create(reservation=reservation)

        assert ticket.reservation == reservation
        assert ticket.used_at is None
        assert ticket.code is not None
        assert ticket.share_token != ticket.code

    def test_reservation_can_have_multiple_tickets(self, event, customer):
        reservation = Reservation.objects.create(customer=customer, event=event, quantity=3)
        Ticket.objects.create(reservation=reservation)
        Ticket.objects.create(reservation=reservation)
        Ticket.objects.create(reservation=reservation)

        assert reservation.tickets.count() == 3

    def test_two_tickets_never_share_the_same_code(self, event, customer):
        reservation_a = Reservation.objects.create(customer=customer, event=event, quantity=1)
        reservation_b = Reservation.objects.create(customer=customer, event=event, quantity=1)

        ticket_a = Ticket.objects.create(reservation=reservation_a)
        ticket_b = Ticket.objects.create(reservation=reservation_b)

        assert ticket_a.code != ticket_b.code


@pytest.mark.django_db
class TestPaymentModel:
    def test_creates_pending_payment_by_default(self, event, customer):
        reservation = Reservation.objects.create(customer=customer, event=event, quantity=1)
        payment = Payment.objects.create(reservation=reservation, amount="70.00")
        assert payment.status == Payment.Status.PENDENTE

    def test_reservation_can_have_multiple_payments(self, event, customer):
        reservation = Reservation.objects.create(customer=customer, event=event, quantity=1)
        Payment.objects.create(reservation=reservation, amount="70.00", status=Payment.Status.RECUSADO)
        Payment.objects.create(reservation=reservation, amount="70.00", status=Payment.Status.CONFIRMADO)

        assert reservation.payments.count() == 2


@pytest.mark.django_db
class TestReservationAPI:
    def test_create_reservation_success(self, api_client, customer, event):
        api_client.force_authenticate(user=customer)
        response = api_client.post('/api/v1/reservations/', {'event': event.id, 'quantity': 2})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['quantity'] == 2
        assert response.data['status'] == Reservation.Status.PENDENTE

    def test_create_reservation_invalid_quantity(self, api_client, customer, event):
        api_client.force_authenticate(user=customer)
        response = api_client.post('/api/v1/reservations/', {'event': event.id, 'quantity': 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_reservation_unpublished_event(self, api_client, customer, event):
        event.is_published = False
        event.save()
        api_client.force_authenticate(user=customer)
        response = api_client.post('/api/v1/reservations/', {'event': event.id, 'quantity': 2})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_reservation_past_event(self, api_client, customer, event):
        event.date = timezone.now() - timedelta(days=1)
        event.save()
        api_client.force_authenticate(user=customer)
        response = api_client.post('/api/v1/reservations/', {'event': event.id, 'quantity': 2})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_reservation_insufficient_capacity(self, api_client, customer, event):
        event.capacity = 1
        event.save()
        api_client.force_authenticate(user=customer)
        response = api_client.post('/api/v1/reservations/', {'event': event.id, 'quantity': 2})
        assert response.status_code == status.HTTP_409_CONFLICT
        
    def test_list_mine_reservations(self, api_client, customer, event):
        Reservation.objects.create(customer=customer, event=event, quantity=1, status=Reservation.Status.PENDENTE, expires_at=timezone.now() + timedelta(minutes=15))
        api_client.force_authenticate(user=customer)
        response = api_client.get('/api/v1/reservations/mine/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_list_mine_reservations_paginates(self, api_client, customer, event):
        for _ in range(11):
            Reservation.objects.create(
                customer=customer, event=event, quantity=1,
                status=Reservation.Status.PENDENTE,
                expires_at=timezone.now() + timedelta(minutes=15),
            )
        api_client.force_authenticate(user=customer)

        response = api_client.get('/api/v1/reservations/mine/')

        assert response.data['count'] == 11
        assert len(response.data['results']) == 10
        assert response.data['next'] is not None

    def test_cancel_reservation_success(self, api_client, customer, event):
        res = Reservation.objects.create(customer=customer, event=event, quantity=1, status=Reservation.Status.PENDENTE, expires_at=timezone.now() + timedelta(minutes=15))
        api_client.force_authenticate(user=customer)
        response = api_client.post(f'/api/v1/reservations/{res.id}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Reservation.Status.CANCELADA

    def test_cancel_reservation_someone_else(self, api_client, customer, organizer, event):
        res = Reservation.objects.create(customer=organizer, event=event, quantity=1, status=Reservation.Status.PENDENTE, expires_at=timezone.now() + timedelta(minutes=15))
        api_client.force_authenticate(user=customer)
        response = api_client.post(f'/api/v1/reservations/{res.id}/cancel/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_already_resolved(self, api_client, customer, event):
        res = Reservation.objects.create(customer=customer, event=event, quantity=1, status=Reservation.Status.PAGA)
        api_client.force_authenticate(user=customer)
        response = api_client.post(f'/api/v1/reservations/{res.id}/cancel/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db(transaction=True)
def test_concurrency_anti_double_sell(organizer):
    from django.db import connection
    
    # Setup objects
    customer1 = User.objects.create_user(email="c1@example.com", first_name="A", last_name="B", password="123")
    customer2 = User.objects.create_user(email="c2@example.com", first_name="C", last_name="D", password="123")
    event = Event.objects.create(
        title="Event",
        date=timezone.now() + timedelta(days=5),
        location="Loc",
        capacity=1,
        price="35.00",
        organizer=organizer,
        external_ref=123,
        is_published=True,
    )
    
    connection.close()

    def make_request(user):
        from rest_framework.test import APIClient
        from django.db import connection
        
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.post('/api/v1/reservations/', {'event': event.id, 'quantity': 1})
        connection.close()
        return resp.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(make_request, customer1)
        f2 = executor.submit(make_request, customer2)

        status_codes = sorted([f1.result(), f2.result()])

    assert status_codes == [201, 409]


@pytest.mark.django_db
class TestShareTicket:
    def test_returns_event_data_without_sensitive_fields(self, api_client, customer, event):
        reserva = Reservation.objects.create(
            customer=customer, event=event, quantity=2,
            status=Reservation.Status.PAGA,
        )
        ticket = Ticket.objects.create(reservation=reserva)

        response = api_client.get(f'/api/v1/reservations/share/{ticket.share_token}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == event.title
        assert response.data['location'] == event.location
        assert response.data['quantity'] == 2
        assert 'code' not in response.data
        assert 'signature' not in response.data
        assert 'customer' not in response.data

    def test_unknown_token_returns_404(self, api_client):
        response = api_client.get(
            '/api/v1/reservations/share/00000000-0000-0000-0000-000000000000/'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.fixture
def paid_ticket(customer, event):
    from reservations.views import confirm_payment_and_generate_ticket

    reserva = Reservation.objects.create(
        customer=customer, event=event, quantity=1,
        status=Reservation.Status.PENDENTE,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    confirm_payment_and_generate_ticket(reserva.id)
    return Ticket.objects.get(reservation=reserva)


@pytest.mark.django_db
class TestConfirmPaymentGeneratesOneTicketPerUnit:
    def test_creates_one_ticket_per_quantity_unit(self, customer, event):
        from reservations.views import confirm_payment_and_generate_ticket

        reserva = Reservation.objects.create(
            customer=customer, event=event, quantity=3,
            status=Reservation.Status.PENDENTE,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        confirm_payment_and_generate_ticket(reserva.id)

        tickets = Ticket.objects.filter(reservation=reserva)
        assert tickets.count() == 3
        assert len({t.code for t in tickets}) == 3
        assert len({t.short_code for t in tickets}) == 3
        assert all(t.signature for t in tickets)


@pytest.mark.django_db
class TestValidateTicket:
    def test_valid_qr_token_liberates_entry(self, api_client, portaria, paid_ticket, event):
        api_client.force_authenticate(user=portaria)

        response = api_client.post('/api/v1/reservations/validate-ticket/', {
            'token': f'{paid_ticket.code}.{paid_ticket.signature}',
            'event_id': event.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'válido'

    def test_valid_short_code_is_case_insensitive(self, api_client, portaria, paid_ticket, event):
        api_client.force_authenticate(user=portaria)

        response = api_client.post('/api/v1/reservations/validate-ticket/', {
            'token': paid_ticket.short_code.lower(),
            'event_id': event.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'válido'

    def test_already_used_returns_409(self, api_client, portaria, paid_ticket, event):
        api_client.force_authenticate(user=portaria)
        payload = {'token': paid_ticket.short_code, 'event_id': event.id}

        api_client.post('/api/v1/reservations/validate-ticket/', payload)
        response = api_client.post('/api/v1/reservations/validate-ticket/', payload)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data['status'] == 'já utilizado'

    def test_wrong_event_returns_400(self, api_client, portaria, paid_ticket, organizer):
        outro_evento = Event.objects.create(
            title="Outro evento", date=timezone.now() + timedelta(days=1),
            location="Y", capacity=10, price="10.00", organizer=organizer,
            external_ref=9999, is_published=True,
        )
        api_client.force_authenticate(user=portaria)

        response = api_client.post('/api/v1/reservations/validate-ticket/', {
            'token': paid_ticket.short_code,
            'event_id': outro_evento.id,
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == 'evento errado'

    def test_unknown_code_returns_404(self, api_client, portaria, event):
        api_client.force_authenticate(user=portaria)

        response = api_client.post('/api/v1/reservations/validate-ticket/', {
            'token': 'ZZZZZZZZZZ',
            'event_id': event.id,
        })

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cliente_cannot_validate(self, api_client, customer, paid_ticket, event):
        api_client.force_authenticate(user=customer)

        response = api_client.post('/api/v1/reservations/validate-ticket/', {
            'token': paid_ticket.short_code,
            'event_id': event.id,
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCheckInProgress:
    def test_counts_validated_and_total_tickets(self, api_client, portaria, paid_ticket, event):
        api_client.force_authenticate(user=portaria)

        response = api_client.get(f'/api/v1/reservations/check-in/{event.id}/')
        assert response.data == {'validados': 0, 'total': 1}

        api_client.post('/api/v1/reservations/validate-ticket/', {
            'token': paid_ticket.short_code, 'event_id': event.id,
        })

        response = api_client.get(f'/api/v1/reservations/check-in/{event.id}/')
        assert response.data == {'validados': 1, 'total': 1}

    def test_cliente_cannot_access(self, api_client, customer, event):
        api_client.force_authenticate(user=customer)
        response = api_client.get(f'/api/v1/reservations/check-in/{event.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
