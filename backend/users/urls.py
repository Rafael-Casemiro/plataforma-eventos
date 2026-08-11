from django.urls import path

from . import views

urlpatterns = [
    path('registro/', views.register, name='auth-registro'),
    path('login/', views.login, name='auth-login'),
]
