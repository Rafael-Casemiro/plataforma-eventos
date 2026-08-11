from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .tmdb_client import TMDbClientError, buscar_filmes_em_cartaz

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