from django.db import models
from django.conf import settings
from events.models import Event
import uuid


class Reservation(models.Model):
     class Status(models.TextChoices):
          PENDENTE = 'pendente', 'Pendente'
          PAGA = 'paga', 'Paga'
          RECUSADA = 'recusada', 'Recusada'
          CANCELADA = 'cancelada', 'Cancelada'

     customer = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
     event = models.ForeignKey(to=Event, on_delete=models.CASCADE, related_name='reservations')
     quantity = models.PositiveIntegerField()
     status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
     created_at = models.DateTimeField(auto_now_add=True)
     expires_at = models.DateTimeField(null=True, blank=True)

class Ticket(models.Model):
     reservation = models.ForeignKey(to=Reservation, on_delete=models.CASCADE, related_name='tickets')
     code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
     signature = models.CharField(max_length=128, blank=True)
     short_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
     used_at = models.DateTimeField(blank=True, null=True)
     share_token = models.UUIDField(default=uuid.uuid4, unique=True)


class Payment(models.Model):
     class Status(models.TextChoices):
          PENDENTE = 'pendente', 'Pendente'
          CONFIRMADO = 'confirmado', 'Confirmado'
          RECUSADO = 'recusado', 'Recusado'

     reservation = models.ForeignKey(to=Reservation, on_delete=models.CASCADE, related_name='payments')
     status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDENTE)
     amount = models.DecimalField(max_digits=8, decimal_places=2)
