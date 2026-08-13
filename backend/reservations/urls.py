from django.urls import path
from .views import reservation, list_my_reservations, cancel_reservation, pay_reservation, stripe_webhook, validate_ticket, share_ticket, check_in_progress

urlpatterns = [
    path('', reservation, name='create-reservation'),
    path('mine/', list_my_reservations, name='list-reservations'),
    path('<int:pk>/cancel/', cancel_reservation, name='cancel-reservation'),
    path('<int:pk>/pay/', pay_reservation, name='pay-reservation'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('validate-ticket/', validate_ticket, name='validate-ticket'),
    path('share/<uuid:share_token>/', share_ticket, name='share-ticket'),
    path('check-in/<int:event_id>/', check_in_progress, name='check-in-progress'),
]
