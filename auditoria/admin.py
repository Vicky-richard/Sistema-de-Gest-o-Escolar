from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('criado_em', 'utilizador', 'accao', 'tabela', 'id_registo',
                    'valor_anterior', 'valor_novo')
    list_filter = ('accao',)

    def has_change_permission(self, request, obj=None):
        return False  # RNF06: os registos não podem ser alterados

    def has_delete_permission(self, request, obj=None):
        return False
