from django.contrib import admin

from .models import AnoLectivo, Atribuicao, Classe, Disciplina, Professor, Turma

admin.site.register([AnoLectivo, Classe, Disciplina, Professor])


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'classe', 'ano_lectivo', 'turno')
    list_filter = ('ano_lectivo', 'classe')


@admin.register(Atribuicao)
class AtribuicaoAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'turma', 'professor')
    list_filter = ('turma__ano_lectivo',)
