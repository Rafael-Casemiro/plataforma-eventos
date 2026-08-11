from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

class CookieJWTAuthentication(JWTAuthentication):
     def enforce_csrf(self, request):
          SessionAuthentication().enforce_csrf(request)

     def authenticate(self, request):
          token = request.COOKIES.get('access')

          if token is None:
               return None

          validated_token = self.get_validated_token(token)
          self.enforce_csrf(request)

          return self.get_user(validated_token), validated_token