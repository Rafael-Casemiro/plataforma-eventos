from django.contrib import admin
from .models import Reservation, Ticket, Payment

class ReservationAdmin(admin.ModelAdmin):
     list_display = ['id', 'customer', 'event', 'quantity', 'status']

     # Filtros e busca
     list_filter = ['status']
     search_fields = ['customer__email', 'event__title']

class TicketAdmin(admin.ModelAdmin):
     list_display = ['id', 'reservation', 'code', 'signature', 'used_at', 'share_token']


     readonly_fields = ['used_at']

class PaymentAdmin(admin.ModelAdmin):
     list_display = ['id', 'reservation', 'status', 'amount']

     list_filter = ['status']
     search_fields = ['reservation__customer__email', 'reservation__event__title']

# Registra a classe no painel administrativo do Django
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Payment, PaymentAdmin)