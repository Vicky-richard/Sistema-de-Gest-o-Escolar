from django.contrib import admin

from .models import Aluno, AlunoEncarregado, Encarregado, Matricula


class AlunoEncarregadoInline(admin.TabularInline):
    model = AlunoEncarregado
    extra = 1


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_nascimento', 'activo')
    search_fields = ('nome', 'doc_identificacao')
    inlines = [AlunoEncarregadoInline]


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'turma', 'tipo', 'estado')
    list_filter = ('ano_lectivo', 'estado')


admin.site.register(Encarregado)
