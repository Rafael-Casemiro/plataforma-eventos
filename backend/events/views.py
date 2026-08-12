from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .tmdb_client import TMDbClientError, buscar_filmes_em_cartaz
from .models import Event
from .serializers import EventSerializer, EventWriteSerializer
from users.permissions import IsOrganizador, IsCliente, IsPortaria

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

@api_view(["GET"])
@permission_classes([AllowAny])
def get_eventos(request):
     eventos = Event.objects.filter(is_published=True)
     serializer = EventSerializer(eventos, many=True)
     return Response({"eventos": serializer.data}, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsOrganizador])
def criar_evento(request):
     serializer = EventWriteSerializer(data=request.data)
     serializer.is_valid(raise_exception=True)

     evento = serializer.save(organizer=request.user)

     response = Response(EventSerializer(evento).data, status=status.HTTP_201_CREATED)
     return response

@api_view(['PUT', 'PATCH'])
@permission_classes([IsOrganizador])
def update_evento(request, pk):
     evento = get_object_or_404(Event, pk=pk)

     if evento.organizer != request.user:
          return Response({"detail": "Você não tem permissão para editar este evento."}, status=status.HTTP_403_FORBIDDEN)

     serializer = EventWriteSerializer(evento, data=request.data, partial=request.method == 'PATCH')
     serializer.is_valid(raise_exception=True)
     evento = serializer.save()

     return Response(EventSerializer(evento).data, status=status.HTTP_200_OK)
