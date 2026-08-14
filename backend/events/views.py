from django.shortcuts import get_object_or_404
from datetime import date as date_cls
from decimal import Decimal, InvalidOperation
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .tmdb_client import TMDbClientError, buscar_filmes_em_cartaz
from .models import Event
from .serializers import EventSerializer, EventWriteSerializer
from users.permissions import IsOrganizador, IsCliente, IsPortaria


class EventPagination(PageNumberPagination):
     page_size = 12
     page_size_query_param = 'page_size'
     max_page_size = 50


@extend_schema(
     responses={200: None},
     description='Lista bruta de filmes em cartaz na TMDb, usada pelo organizador como base de conteúdo ao criar um evento.',
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def catalogo(request):
     try:
          filmes = buscar_filmes_em_cartaz()
     except TMDbClientError:
          return Response(
               {"detail": "Não foi possível consultar o catálogo da TMDb."},
               status=502
          )
     return Response(filmes)

@extend_schema(
     responses={200: EventSerializer(many=True)},
     description='Catálogo público e paginado de eventos publicados. Resposta real é paginada (`{count, next, previous, results}`).',
     parameters=[
          OpenApiParameter('search', str, description='Filtra por título (case-insensitive, contém).'),
          OpenApiParameter('date', str, description='Filtra por data exata, formato ISO (YYYY-MM-DD).'),
          OpenApiParameter('price_min', str, description='Preço mínimo.'),
          OpenApiParameter('price_max', str, description='Preço máximo.'),
          OpenApiParameter('page', int, description='Número da página.'),
     ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_eventos(request):
     agora = timezone.now()

     eventos = Event.objects.filter(is_published=True).annotate(
          reservado=Sum(
               'reservations__quantity',
               filter=Q(reservations__status='paga') | Q(
                    reservations__status='pendente',
                    reservations__expires_at__gt=agora,
               ),
          )
     ).order_by('date')

     search = request.query_params.get('search')
     if search:
          eventos = eventos.filter(title__icontains=search)

     date = request.query_params.get('date')
     if date:
          try:
               date_cls.fromisoformat(date)
          except ValueError:
               return Response({"detail": "date inválido."}, status=400)
          eventos = eventos.filter(date__date=date)

     price_min = request.query_params.get('price_min')
     if price_min:
          try:
               price_min = Decimal(price_min)
          except InvalidOperation:
               return Response({"detail": "price_min inválido."}, status=400)
          eventos = eventos.filter(price__gte=price_min)

     price_max = request.query_params.get('price_max')
     if price_max:
          try:
               price_max = Decimal(price_max)
          except InvalidOperation:
               return Response({"detail": "price_max inválido"}, status=400)
          eventos = eventos.filter(price__lte=price_max)

     
     paginator = EventPagination()
     page = paginator.paginate_queryset(eventos, request)
     serializer = EventSerializer(page, many=True)
     return paginator.get_paginated_response(serializer.data)

@extend_schema(
     responses={200: EventSerializer(many=True)},
     description='Eventos do organizador autenticado (não paginado). Resposta real: `{"eventos": [...]}`.',
)
@api_view(['GET'])
@permission_classes([IsOrganizador])
def get_eventos_organizador(request):
     eventos = Event.objects.filter(organizer=request.user)

     serializer = EventSerializer(eventos, many=True)
     return Response({"eventos": serializer.data}, status=status.HTTP_200_OK)

@extend_schema(request=EventWriteSerializer, responses={201: EventSerializer})
@api_view(["POST"])
@permission_classes([IsOrganizador])
def criar_evento(request):
     serializer = EventWriteSerializer(data=request.data)
     serializer.is_valid(raise_exception=True)

     evento = serializer.save(organizer=request.user)

     response = Response(EventSerializer(evento).data, status=status.HTTP_201_CREATED)
     return response

@extend_schema(
     request=EventWriteSerializer,
     responses={200: EventSerializer, 204: None, 403: None},
     description='PUT/PATCH atualizam o evento (apenas o organizador dono); DELETE remove.',
)
@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsOrganizador])
def update_evento(request, pk):
     evento = get_object_or_404(Event, pk=pk)

     if evento.organizer != request.user:
          return Response({"detail": "Você não tem permissão para editar este evento."}, status=status.HTTP_403_FORBIDDEN)

     if request.method == 'DELETE':
          evento.delete()
          return Response(status=status.HTTP_204_NO_CONTENT)

     serializer = EventWriteSerializer(evento, data=request.data, partial=request.method == 'PATCH')
     serializer.is_valid(raise_exception=True)
     evento = serializer.save()

     return Response(EventSerializer(evento).data, status=status.HTTP_200_OK)
