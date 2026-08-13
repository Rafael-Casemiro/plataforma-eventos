from django.urls import path
from .views import catalogo, get_eventos, criar_evento, update_evento, get_eventos_organizador

urlpatterns = [
    path('catalog/', catalogo, name='listar-catalogo'),
    path('', get_eventos, name='listar-eventos'),
    path('mine/', get_eventos_organizador, name='listar-eventos-organizador'),
    path('create/', criar_evento, name='criar-evento'),
    path('<int:pk>/', update_evento, name='atualizar-evento')
]
