import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.utils import timezone

from events.models import Event
from reservations.models import Payment, Reservation, Ticket

User = get_user_model()


@pytest.fixture
def event(db):
    organizer = User.objects.create_user(
        email="organizador_res@example.com",
        first_name="Rafael",
        last_name="Casemiro",
        password="senha123",
        role=User.Role.ORGANIZADOR,
    )
    return Event.objects.create(
        title="Duna: Parte Dois",
        date=timezone.now(),
        location="Cine Verzel",
        capacity=100,
        price="35.00",
        organizer=organizer,
        external_ref=693134,
        is_published=True,
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        email="cliente_res@example.com",
        first_name="Joana",
        last_name="Souza",
        password="senha123",
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

    def test_reservation_can_only_have_one_ticket(self, event, customer):
        reservation = Reservation.objects.create(customer=customer, event=event, quantity=1)
        Ticket.objects.create(reservation=reservation)

        with pytest.raises(IntegrityError):
            Ticket.objects.create(reservation=reservation)

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
