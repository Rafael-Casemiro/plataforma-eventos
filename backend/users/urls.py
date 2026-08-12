from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='auth-registro'),
    path('login/', views.login, name='auth-login'),
    path('logout/', views.logout, name='logout'),
    path('refresh/', views.refresh, name='auth-refresh'),
    path('me/', views.me, name='auth-me')
]
