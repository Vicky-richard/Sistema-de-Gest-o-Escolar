from django.conf import settings
from django.db import models


class LogAuditoria(models.Model):
    """RNF06: registo das acções críticas."""
    id = models.BigAutoField(primary_key=True)
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT)
    accao = models.CharField(max_length=30)
    tabela = models.CharField(max_length=50)
    id_registo = models.IntegerField()
    valor_anterior = models.CharField(max_length=500, blank=True)
    valor_novo = models.CharField(max_length=500, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'logs_auditoria'
        ordering = ['-criado_em']
        verbose_name = 'registo de auditoria'
        verbose_name_plural = 'registos de auditoria'

    def __str__(self):
        return f'{self.criado_em:%d/%m/%Y %H:%M} {self.accao} {self.tabela}#{self.id_registo}'
