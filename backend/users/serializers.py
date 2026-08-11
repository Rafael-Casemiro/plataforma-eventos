from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
     class Meta:
          model = User
          fields = [
               'id',
               'email',
               'first_name',
               'last_name',
               'role',
               'is_staff',
               'is_active',
               'created_at',
               'updated_at',
          ]

          read_only_fields = [
               'id',
               'created_at',
               'updated_at',
          ]

class UserCreateSerializer(serializers.ModelSerializer):
     password = serializers.CharField(
          write_only=True,
          min_length=8
     )
     password_confirm = serializers.CharField(
          write_only=True,
          min_length=8
     )

     class Meta:
          model = User
          fields = [
               'email',
               'first_name',
               'last_name',
               'password',
               'password_confirm',
          ]

     def validate(self, attrs):
          if attrs['password'] != attrs['password_confirm']:
               raise serializers.ValidationError({
                    'password_confirm': 'As senhas não coincidem.'
               })
          return attrs

     def create(self, validated_data):
          validated_data.pop('password_confirm')

          return User.objects.create_user(
               **validated_data
          )

class LoginSerializer(serializers.Serializer):
     email = serializers.EmailField()
     password = serializers.CharField(
          write_only = True
     )

     def validate(self, attrs):
          email = attrs.get('email')
          password = attrs.get('password')

          user = authenticate(
               self.context.get('request'),
               email=email,
               password=password
          )

          if user is None:
               raise serializers.ValidationError(
                    'Email ou senha inválidos.'
               )

          if not user.is_active:
               raise serializers.ValidationError(
                    'Usuário inativo'
               )

          attrs['user'] = user

          return attrs