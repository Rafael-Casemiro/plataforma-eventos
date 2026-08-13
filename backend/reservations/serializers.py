from rest_framework import serializers
from .models import Reservation, Ticket


class TicketSerializer(serializers.ModelSerializer):
     qr_token = serializers.SerializerMethodField()

     class Meta:
          model = Ticket
          fields = ['id', 'code', 'used_at', 'share_token', 'qr_token', 'short_code']

     def get_qr_token(self, obj):
          return f"{obj.code}.{obj.signature}"


class ReservationSerializer(serializers.ModelSerializer):
     ticket = TicketSerializer(read_only=True)
     event_title = serializers.CharField(source='event.title', read_only=True)
     event_date = serializers.DateTimeField(source='event.date', read_only=True)
     event_location = serializers.CharField(source='event.location', read_only=True)
     event_poster_path = serializers.CharField(source='event.poster_path', read_only=True)

     class Meta:
          model = Reservation

          fields = [
               'id',
               'customer',
               'event',
               'event_title',
               'event_date',
               'event_location',
               'event_poster_path',
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


class SharedTicketSerializer(serializers.Serializer):
     title = serializers.CharField(source='reservation.event.title')
     date = serializers.DateTimeField(source='reservation.event.date')
     location = serializers.CharField(source='reservation.event.location')
     poster_path = serializers.CharField(source='reservation.event.poster_path')
     quantity = serializers.IntegerField(source='reservation.quantity')