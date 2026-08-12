from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie

from .serializers import UserSerializer, UserCreateSerializer, LoginSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
     serializer = UserCreateSerializer(data=request.data)

     serializer.is_valid(raise_exception=True)
     user = serializer.save()

     return Response(
          {
               "message": "Usuário criado com sucesso",
               "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
               }
          },
          status=status.HTTP_201_CREATED
     )

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
     serializer = LoginSerializer(data=request.data, context={'request': request})

     serializer.is_valid(raise_exception=True)

     user = serializer.validated_data['user']

     refresh = RefreshToken.for_user(user)

     response = Response(
         {
              "user": UserSerializer(user).data
         },
         status=status.HTTP_200_OK
     )

     response.set_cookie(
          'access', str(refresh.access_token),
          httponly=True, secure=not settings.DEBUG, samesite='Lax',
     )
     response.set_cookie(
          'refresh', str(refresh),
          httponly=True, secure=not settings.DEBUG, samesite='Lax',
     )


     return response



@api_view(['POST'])
@permission_classes([AllowAny])
def refresh(request):
     refresh_token = request.COOKIES.get('refresh')

     if not refresh_token:
          return Response(
               {
                    "detail": "Refresh token não encontrado."
               },
               status=status.HTTP_401_UNAUTHORIZED
          )

     try:
          refresh = RefreshToken(refresh_token)

          access_token = refresh.access_token

          response = Response(
               {
                    "message": "Access token renovado com sucesso."
               },
               status=status.HTTP_200_OK
          )

          response.set_cookie(
               'access',
               str(access_token),
               httponly=True,
               secure=not settings.DEBUG,
               samesite='Lax',
          )

          return response
     except TokenError:
          return Response(
               {
                    "detail": "Refresh token inválido ou expirado."
               },
               status=status.HTTP_401_UNAUTHORIZED
          )
@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
     response = Response(
          {
               "message": "Logout realizado com sucesso."
          },
          status=status.HTTP_200_OK
     )

     response.delete_cookie(
          'access',
          samesite='Lax'
     )

     response.delete_cookie(
          'refresh',
          samesite='Lax'
     )

     return response

@ensure_csrf_cookie
@api_view(['GET'])
def me(request):

     response = Response(
          {
               "user": UserSerializer(request.user).data
          }
     )

     return response