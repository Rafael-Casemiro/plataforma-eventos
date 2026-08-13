import stripe
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .serializers import ReservationSerializer, ReservationWriteSerializer, SharedTicketSerializer
from .models import Reservation
from events.models import Event
from users.permissions import IsPortaria


class ReservationPagination(PageNumberPagination):
     page_size = 10
     page_size_query_param = 'page_size'
     max_page_size = 50


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reservation(request):
     serializer = ReservationWriteSerializer(data=request.data)
     serializer.is_valid(raise_exception=True)

     event_obj = serializer.validated_data['event']
     quantity = serializer.validated_data['quantity']

     agora = timezone.now()

     with transaction.atomic():
          try:
               event_lock = Event.objects.select_for_update().get(id=event_obj.id, is_published=True)
          except Event.DoesNotExist:
               return Response(status=status.HTTP_404_NOT_FOUND)

          # Evento já passou
          if event_lock.date < agora:
               return Response({"detail": "Não é possível reservar ingressos para um evento que já passou."}, status=status.HTTP_400_BAD_REQUEST)

          # Soma APENAS as ativas (pagas ou pendentes NÃO expiradas)
          ocupados = Reservation.objects.filter(
               event=event_lock
          ).filter(
               models.Q(status=Reservation.Status.PAGA) |
               models.Q(status=Reservation.Status.PENDENTE, expires_at__gt=agora)
          ).aggregate(total=Sum('quantity'))['total'] or 0

          ingressos_disponiveis = event_lock.capacity - ocupados

          if quantity > ingressos_disponiveis:
               return Response(
                    {"detail": f"Restam apenas {ingressos_disponiveis} vaga(s) para este evento."},
                    status=status.HTTP_409_CONFLICT
               )
          
          expires_at = agora + timedelta(minutes=15)

          reserva = Reservation.objects.create(
               customer=request.user,
               event=event_lock,
               quantity=quantity,
               status=Reservation.Status.PENDENTE,
               expires_at=expires_at
          )

     response_serializer = ReservationSerializer(reserva)
     return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_reservations(request):
     agora = timezone.now()
     
     # Lazy Expiration: Atualiza status das reservas vencidas antes de retornar
     reservas_vencidas = Reservation.objects.filter(
          customer=request.user,
          status=Reservation.Status.PENDENTE,
          expires_at__lte=agora
     )
     reservas_vencidas.update(status=Reservation.Status.CANCELADA)

     reservas = Reservation.objects.filter(
          customer=request.user
     ).select_related('event').prefetch_related('tickets').order_by('-created_at')
     paginator = ReservationPagination()
     page = paginator.paginate_queryset(reservas, request)
     serializer = ReservationSerializer(page, many=True)

     return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_reservation(request, pk):
     try:
          reserva = Reservation.objects.get(pk=pk, customer=request.user)
     except Reservation.DoesNotExist:
          return Response(status=status.HTTP_404_NOT_FOUND)

     agora = timezone.now()

     # Aplica lazy expiration
     if reserva.status == Reservation.Status.PENDENTE and reserva.expires_at and reserva.expires_at <= agora:
          reserva.status = Reservation.Status.CANCELADA
          reserva.save(update_fields=['status'])

     if reserva.status in [Reservation.Status.PAGA, Reservation.Status.RECUSADA]:
          return Response({"detail": f"Não é possível cancelar uma reserva {reserva.status}."}, status=status.HTTP_400_BAD_REQUEST)

     if reserva.status == Reservation.Status.PENDENTE:
          reserva.status = Reservation.Status.CANCELADA
          reserva.save(update_fields=['status'])

     serializer = ReservationSerializer(reserva)
     return Response(serializer.data, status=status.HTTP_200_OK)


import hmac
import hashlib
import secrets
from django.conf import settings
from .models import Payment, Ticket

SHORT_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
SHORT_CODE_LENGTH = 10


def _gerar_short_code():
     while True:
          codigo = ''.join(secrets.choice(SHORT_CODE_ALPHABET) for _ in range(SHORT_CODE_LENGTH))
          if not Ticket.objects.filter(short_code=codigo).exists():
               return codigo

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_reservation(request, pk):
     try:
          reserva = Reservation.objects.get(pk=pk, customer=request.user)
     except Reservation.DoesNotExist:
          return Response(status=status.HTTP_404_NOT_FOUND)

     agora = timezone.now()

     if reserva.status == Reservation.Status.PENDENTE and reserva.expires_at and reserva.expires_at <= agora:
          reserva.status = Reservation.Status.CANCELADA
          reserva.save(update_fields=['status'])
          return Response({"detail": "Reserva expirada."}, status=status.HTTP_400_BAD_REQUEST)

     if reserva.status != Reservation.Status.PENDENTE:
          return Response({"detail": f"A reserva está {reserva.status} e não pode ser paga."}, status=status.HTTP_400_BAD_REQUEST)

     simulate = request.data.get('simulate', 'success')
     amount_due = reserva.quantity * reserva.event.price

     if simulate == 'stripe':
          stripe.api_key = settings.STRIPE_SECRET_KEY

          session = stripe.checkout.Session.create(
               payment_method_types=['card'],
               line_items=[{
                    'price_data': {
                         'currency': 'brl',
                         'product_data': {'name': reserva.event.title},
                         'unit_amount': int(reserva.event.price * 100),
                    },
                    'quantity': reserva.quantity,
               }],
               mode='payment',
               success_url=f"{settings.FRONTEND_URL}/reservas?status=success",
               cancel_url=f"{settings.FRONTEND_URL}/reservas?status=canceled",
               client_reference_id=str(reserva.id),
          )

          return Response({"checkout_url": session.url})

     with transaction.atomic():
          if simulate == 'fail':
               Payment.objects.create(reservation=reserva, amount=amount_due, status=Payment.Status.RECUSADO)
               reserva.status = Reservation.Status.RECUSADA
               reserva.save(update_fields=['status'])
               serializer = ReservationSerializer(reserva)
               return Response(serializer.data, status=status.HTTP_200_OK)
          
          # simulate == 'success'
          confirm_payment_and_generate_ticket(reserva.id)
          reserva.refresh_from_db()

     serializer = ReservationSerializer(reserva)
     return Response(serializer.data, status=status.HTTP_200_OK)

def confirm_payment_and_generate_ticket(reserva_id):
     with transaction.atomic():
          try:
               reserva = Reservation.objects.select_for_update().get(
                    id=reserva_id, status=Reservation.Status.PENDENTE
               )
          except Reservation.DoesNotExist:
               return

          if reserva.expires_at and reserva.expires_at <= timezone.now():
               reserva.status = Reservation.Status.CANCELADA
               reserva.save(update_fields=['status'])
               return

          amount_due = reserva.quantity * reserva.event.price
          Payment.objects.create(reservation=reserva, amount=amount_due, status=Payment.Status.CONFIRMADO)
          reserva.status = Reservation.Status.PAGA
          reserva.save(update_fields=['status'])

          # Um ticket por unidade reservada — cada um validado individualmente na portaria
          for _ in range(reserva.quantity):
               ticket = Ticket.objects.create(reservation=reserva)
               payload = f"{ticket.code}:{reserva.event_id}".encode('utf-8')
               key = settings.SECRET_KEY.encode('utf-8')
               signature = hmac.new(key, payload, hashlib.sha256).hexdigest()

               ticket.signature = signature
               ticket.short_code = _gerar_short_code()
               ticket.save(update_fields=['signature', 'short_code'])

@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
     payload = request.body
     sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

     try:
          endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
          event = stripe.Webhook.construct_event(
               payload, sig_header, endpoint_secret
          )
     
     except (ValueError, stripe.error.SignatureVerificationError):
          return Response(status=status.HTTP_400_BAD_REQUEST)
     
     if event['type'] == 'checkout.session.completed':
          session = event['data']['object']
          reserva_id = getattr(session, 'client_reference_id', None)

          if reserva_id:
               confirm_payment_and_generate_ticket(reserva_id)
     
     return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsPortaria])
def validate_ticket(request):
     token = request.data.get('token', '').strip()
     event_id = request.data.get('event_id')

     if not token or not event_id:
          return Response({"detail": "Token e event_id são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

     with transaction.atomic():
          if '.' in token:
               parts = token.split('.')
               if len(parts) != 2:
                    return Response({"status": "inválido", "detail": "Formato de token inválido."}, status=status.HTTP_400_BAD_REQUEST)

               ticket_code, signature = parts

               try:
                    ticket = Ticket.objects.select_for_update().get(code=ticket_code)
               except Ticket.DoesNotExist:
                    return Response({"status": "inválido", "detail": "Ingresso não encontrado."}, status=status.HTTP_404_NOT_FOUND)

               payload = f"{ticket_code}:{ticket.reservation.event_id}".encode('utf-8')
               key = settings.SECRET_KEY.encode('utf-8')
               expected_signature = hmac.new(key, payload, hashlib.sha256).hexdigest()

               if not hmac.compare_digest(signature, expected_signature):
                    return Response({"status": "inválido", "detail": "Assinatura digital não confere."}, status=status.HTTP_400_BAD_REQUEST)
          else:
               try:
                    ticket = Ticket.objects.select_for_update().get(short_code=token.upper())
               except Ticket.DoesNotExist:
                    return Response({"status": "inválido", "detail": "Ingresso não encontrado."}, status=status.HTTP_404_NOT_FOUND)

          if str(ticket.reservation.event_id) != str(event_id):
               return Response({"status": "evento errado", "detail": "Este ingresso pertence a outro evento."}, status=status.HTTP_400_BAD_REQUEST)

          if ticket.used_at is not None:
               return Response({"status": "já utilizado", "detail": "Ingresso já utilizado."}, status=status.HTTP_409_CONFLICT)

          ticket.used_at = timezone.now()
          ticket.save(update_fields=['used_at'])

     return Response({"status": "válido", "detail": "Entrada liberada!"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsPortaria])
def check_in_progress(request, event_id):
     tickets = Ticket.objects.filter(reservation__event_id=event_id)
     total = tickets.count()
     validados = tickets.filter(used_at__isnull=False).count()

     return Response({"validados": validados, "total": total}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def share_ticket(request, share_token):
     try:
          ticket = Ticket.objects.select_related('reservation__event').get(share_token=share_token)
     except Ticket.DoesNotExist:
          return Response(status=status.HTTP_404_NOT_FOUND)

     serializer = SharedTicketSerializer(ticket)
     return Response(serializer.data, status=status.HTTP_200_OK)