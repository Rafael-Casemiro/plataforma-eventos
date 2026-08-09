from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("O campo de email é obrigatório.")
        if not first_name:
            raise ValueError("O campo de nome é obrigatório")
        if not last_name:
            raise ValueError("O campo de sobrenome é obrigatório")
        
        email = self.normalize_email(email)

        user = self.model(
            email = email,
            first_name = first_name,
            last_name = last_name,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ORGANIZADOR)


        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True')
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
         ORGANIZADOR =  "organizador", "Organizador"
         CLIENTE = "cliente", "Cliente"
         PORTARIA = "portaria", "Portaria"
    
    email = models.EmailField(unique=True, verbose_name="email")
    first_name = models.CharField(max_length=255, verbose_name="Nome")
    last_name = models.CharField(max_length=255, verbose_name="Sobrenome")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENTE)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.email