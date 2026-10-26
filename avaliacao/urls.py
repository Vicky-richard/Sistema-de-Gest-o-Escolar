from django.urls import path

from . import views

urlpatterns = [
    path('lancar/<int:atribuicao_id>/<int:trimestre>/', views.lancar_notas,
         name='lancar_notas'),
    path('pauta/<int:turma_id>/<int:trimestre>/', views.ver_pauta, name='ver_pauta'),
    path('pauta/<int:turma_id>/<int:trimestre>/fechar/', views.fechar_pauta,
         name='fechar_pauta'),
    path('minhas/', views.consultar_notas, name='consultar_notas'),
]
