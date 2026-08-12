from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
     class Meta:
          model = Event
          fields = [
               'id',
               'title',
               'organizer',
               'description',
               'date',
               'location',
               'capacity',
               'price',
               'external_ref',
               'external_title',
               'poster_path',
               'is_published',
               'created_at',
               'updated_at',
          ]

          read_only_fields = [
               'organizer',
               'created_at',
               'updated_at',
          ]

class EventWriteSerializer(serializers.ModelSerializer):
     class Meta:
          model = Event
          fields = [
                    'title',
                    'description',
                    'date',
                    'location',
                    'capacity',
                    'price',
                    'external_ref',
                    'external_title',
                    'poster_path',
                    'is_published',
               ]

          

