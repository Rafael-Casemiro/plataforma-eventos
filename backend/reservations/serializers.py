from rest_framework import serializers
from .models import Reservation, Ticket


class TicketSerializer(serializers.ModelSerializer):
     qr_token = serializers.SerializerMethodField()

     class Meta:
          model = Ticket
          fields = ['id', 'code', 'used_at', 'share_token', 'qr_token']

     def get_qr_token(self, obj):
          return f"{obj.code}.{obj.signature}"


class ReservationSerializer(serializers.ModelSerializer):
     ticket = TicketSerializer(read_only=True)

     class Meta:
          model = Reservation

          fields = [
               'id',
               'customer',
               'event',
               'quantity',
               'status',
               'created_at',
               'expires_at',
               'ticket',
          ]

          read_only_fields = [
               'customer',
               'created_at',
               'expires_at',
          ]

class ReservationWriteSerializer(serializers.ModelSerializer):
     quantity = serializers.IntegerField(min_value=1)

     class Meta:
          model = Reservation

          fields = [
               'event',
               'quantity',
          ]