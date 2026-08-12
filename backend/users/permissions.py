from rest_framework import permissions


class HasRole(permissions.BasePermission):
     required_role = None

     def has_permission(self, request, view):
          if not request.user or not request.user.is_authenticated:
               return False

          try:
               return request.user.role == self.required_role
          except AttributeError:
               return False


class IsOrganizador(HasRole):
     required_role = 'organizador'


class IsPortaria(HasRole):
     required_role = 'portaria'

class IsCliente(HasRole):
     required_role = 'cliente'