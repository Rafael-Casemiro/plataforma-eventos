from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User

class CustomUserAdmin(UserAdmin):
     add_form = CustomUserCreationForm
     form = CustomUserChangeForm
     model = User

     list_display = ['id', 'email', 'first_name', 'last_name', 'is_staff']

     search_fields = ['email', 'first_name', 'last_name']

     ordering = ['id']


     fieldsets = (
          (None, {'fields': ('email', 'password')}),

          # Campo de informações pessoais
          ('Informações pessoais', {'fields': (
               'first_name', 'last_name'
          )}),

          # Permissões de usuários
          ('Permissões', {'fields': ('is_staff', 'is_superuser', 'role')}),

          # Datas
          ('Datas', {'fields': ('created_at', 'updated_at')})
     )

     add_fieldsets = (
          (None, {
               'classes': ('wide',),
               'fields': (
                    'email', 'first_name', 'last_name',
                    'role', 'password1', 'password2',
               ),
          }),
     )

     readonly_fields = ('created_at', 'updated_at')


# Registra a classe no painel administrativo do Django
admin.site.register(User, CustomUserAdmin)