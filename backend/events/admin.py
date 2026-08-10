from django.contrib import admin
from .models import Event

class EventAdmin(admin.ModelAdmin):
     list_display = ['id', 'title', 'organizer', 'date', 'location', 'price', 'is_published', 'created_at']

     # Filtros e busca
     list_filter = ['is_published']
     search_fields = ['title', 'external_title']

     readonly_fields = ['created_at', 'updated_at']

# Registra a classe no painel administrativo do Django
admin.site.register(Event, EventAdmin)