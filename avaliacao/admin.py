from django.contrib import admin

from .models import Nota, Pauta


@admin.register(Pauta)
class PautaAdmin(admin.ModelAdmin):
    list_display = ('turma', 'trimestre', 'estado', 'fechada_por', 'fechada_em')


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'atribuicao', 'trimestre', 'valor')
    list_filter = ('trimestre', 'atribuicao__disciplina')
