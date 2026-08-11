from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

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

