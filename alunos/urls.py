from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista_alunos, name='lista_alunos'),
    path('novo/', views.registar_aluno, name='registar_aluno'),
]
