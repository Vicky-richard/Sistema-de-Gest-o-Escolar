from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('entrar/', views.entrar, name='login'),
    path('sair/', LogoutView.as_view(), name='logout'),
    path('', views.painel, name='painel'),
]
