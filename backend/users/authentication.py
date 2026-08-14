from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CookieJWTAuthentication(JWTAuthentication):
     def enforce_csrf(self, request):
          SessionAuthentication().enforce_csrf(request)

     def authenticate(self, request):
          token = request.COOKIES.get('access')

          if token is None:
               return None

          try:
               validated_token = self.get_validated_token(token)
          except InvalidToken:
               return None
          self.enforce_csrf(request)
          return self.get_user(validated_token), validated_token


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
     target_class = 'users.authentication.CookieJWTAuthentication'
     name = 'cookieAuth'

     def get_security_definition(self, auto_schema):
          return {
               'type': 'apiKey',
               'in': 'cookie',
               'name': 'access',
               'description': 'JWT em cookie httpOnly, obtido via POST /api/v1/auth/login/.',
          }


          