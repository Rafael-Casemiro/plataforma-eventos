from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
     vagas_disponiveis = serializers.SerializerMethodField()

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
               'vagas_disponiveis',
          ]

          read_only_fields = [
               'organizer',
               'created_at',
               'updated_at',
          ]

     def get_vagas_disponiveis(self, obj) -> int:
          reservado = getattr(obj, 'reservado', None) or 0
          return max(obj.capacity - reservado, 0)

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

          

