from django.urls import path
from .views import catalogo

urlpatterns = [
    path('catalog/', catalogo, name='listar-catalogo')
]
