"""Padrão Observer: os sinais do Django notificam a auditoria das alterações."""
from decimal import Decimal

from django.db.models.signals import pre_save
from django.dispatch import receiver

from avaliacao.models import Nota

from .models import LogAuditoria


@receiver(pre_save, sender=Nota)
def registar_alteracao_nota(sender, instance, **kwargs):
    if instance.pk is None:
        return  # nota nova: não há valor anterior
    anterior = Nota.objects.filter(pk=instance.pk).values_list(
        'valor', flat=True).first()
    if anterior is not None and anterior != instance.valor:
        LogAuditoria.objects.create(
            utilizador=getattr(instance, 'alterado_por', None) or instance.lancado_por,
            accao='ALTERAR_NOTA', tabela='notas', id_registo=instance.pk,
            valor_anterior=formatar_nota(anterior),
            valor_novo=formatar_nota(instance.valor) + getattr(instance, 'justificacao', ''))


def formatar_nota(valor):
    """Formato único das notas no log (ex.: 9 -> '9.0')."""
    return f'{Decimal(valor):.1f}'
