from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from events.models import Event
from events.tmdb_client import TMDbClientError, buscar_filmes_em_cartaz
from reservations.models import Payment, Reservation
from reservations.views import confirm_payment_and_generate_ticket

User = get_user_model()

SEED_PASSWORD = 'senha123'

ORGANIZADORES = [
    ('organizador1.seed@example.com', 'Marina', 'Souza'),
    ('organizador2.seed@example.com', 'Pedro', 'Lima'),
]
CLIENTES = [
    ('cliente1.seed@example.com', 'Ana', 'Silva'),
    ('cliente2.seed@example.com', 'Bruno', 'Costa'),
    ('cliente3.seed@example.com', 'Carla', 'Reis'),
]
PORTARIA = ('portaria1.seed@example.com', 'Diego', 'Alves')

SEED_EMAILS = (
    [email for email, _, _ in ORGANIZADORES]
    + [email for email, _, _ in CLIENTES]
    + [PORTARIA[0]]
)


class Command(BaseCommand):
    help = 'Popula o banco com usuarios, eventos e reservas de demonstracao.'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._limpar()

            organizadores = [
                self._criar_usuario(email, first, last, User.Role.ORGANIZADOR)
                for email, first, last in ORGANIZADORES
            ]
            clientes = [
                self._criar_usuario(email, first, last, User.Role.CLIENTE)
                for email, first, last in CLIENTES
            ]
            portaria = self._criar_usuario(*PORTARIA, User.Role.PORTARIA)

            eventos = self._criar_eventos(organizadores)
            self._criar_reservas(clientes, eventos)

        self.stdout.write(self.style.SUCCESS('Seed concluido.'))
        self._imprimir_credenciais(organizadores + clientes + [portaria])

    def _limpar(self):
        User.objects.filter(email__in=SEED_EMAILS).delete()

    def _criar_usuario(self, email, first_name, last_name, role):
        return User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=SEED_PASSWORD,
            role=role,
        )

    def _criar_eventos(self, organizadores):
        try:
            filmes = buscar_filmes_em_cartaz()
        except TMDbClientError as exc:
            raise CommandError(
                'Nao foi possivel buscar filmes na TMDb. Verifique TMDB_API_KEY.'
            ) from exc

        agora = timezone.now()
        eventos = []
        for indice, filme in enumerate(filmes[:6]):
            organizador = organizadores[indice % len(organizadores)]
            evento = Event.objects.create(
                title=filme['titulo'],
                description=filme['sinopse'],
                date=agora + timedelta(days=3 + indice),
                location='Cine Sede',
                capacity=50,
                price=Decimal('35.00'),
                organizer=organizador,
                external_ref=filme['id'],
                external_title=filme['titulo'],
                poster_path=filme['poster_path'] or '',
                is_published=indice < 4,
            )
            eventos.append(evento)
        return eventos

    def _criar_reservas(self, clientes, eventos):
        if len(eventos) < 2:
            return

        Reservation.objects.create(
            customer=clientes[0],
            event=eventos[0],
            quantity=1,
            status=Reservation.Status.PENDENTE,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        reserva_paga = Reservation.objects.create(
            customer=clientes[1],
            event=eventos[0],
            quantity=2,
            status=Reservation.Status.PENDENTE,
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        confirm_payment_and_generate_ticket(reserva_paga.id)

        reserva_recusada = Reservation.objects.create(
            customer=clientes[2],
            event=eventos[1],
            quantity=1,
            status=Reservation.Status.RECUSADA,
        )
        Payment.objects.create(
            reservation=reserva_recusada,
            amount=reserva_recusada.quantity * eventos[1].price,
            status=Payment.Status.RECUSADO,
        )

        Reservation.objects.create(
            customer=clientes[0],
            event=eventos[1],
            quantity=1,
            status=Reservation.Status.CANCELADA,
        )

    def _imprimir_credenciais(self, usuarios):
        self.stdout.write('')
        self.stdout.write(f'Usuarios criados (senha para todos: {SEED_PASSWORD}):')
        for usuario in usuarios:
            self.stdout.write(f'  {usuario.email} - {usuario.get_role_display()}')
