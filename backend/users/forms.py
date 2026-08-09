from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
     # Formulário  para criação de novos usuários
     class Meta:
          model = User
          fields = ('email', 'first_name', 'last_name', 'role')

class CustomUserChangeForm(UserChangeForm):
     class Meta:
          model = User
          fields = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser')