from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from academico.models import Atribuicao, Turma
from alunos.models import Matricula


class Pauta(models.Model):
    class Estado(models.TextChoices):
        ABERTA = 'Aberta'
        FECHADA = 'Fechada'

    turma = models.ForeignKey(Turma, on_delete=models.PROTECT)
    trimestre = models.PositiveSmallIntegerField()
    estado = models.CharField(max_length=10, choices=Estado.choices,
                              default=Estado.ABERTA)
    fechada_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    blank=True, on_delete=models.PROTECT)
    fechada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pautas'
        constraints = [
            models.UniqueConstraint(fields=['turma', 'trimestre'], name='uq_pauta'),
            models.CheckConstraint(condition=models.Q(trimestre__range=(1, 3)),
                                   name='ck_pauta_trimestre')]

    def __str__(self):
        return f'Pauta {self.turma} — {self.trimestre}.º trimestre'

    def esta_fechada(self):
        return self.estado == self.Estado.FECHADA


def validar_valor_nota(valor):
    """RN03: escala de 0 a 20, com no máximo uma casa decimal."""
    if valor is None or not (Decimal('0') <= valor <= Decimal('20')):
        raise ValidationError('A nota deve estar entre 0 e 20.')
    if valor != valor.quantize(Decimal('0.1')):
        raise ValidationError('A nota só pode ter uma casa decimal.')


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.PROTECT,
                                  related_name='notas')
    atribuicao = models.ForeignKey(Atribuicao, on_delete=models.PROTECT,
                                   related_name='notas')
    trimestre = models.PositiveSmallIntegerField()
    valor = models.DecimalField(max_digits=3, decimal_places=1,
                                validators=[validar_valor_nota])
    lancado_por = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.PROTECT)
    lancado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notas'
        constraints = [
            models.UniqueConstraint(fields=['matricula', 'atribuicao', 'trimestre'],
                                    name='uq_nota'),
            models.CheckConstraint(condition=models.Q(valor__gte=0, valor__lte=20),
                                   name='ck_nota_valor'),
            models.CheckConstraint(condition=models.Q(trimestre__range=(1, 3)),
                                   name='ck_nota_trimestre')]

    def __str__(self):
        return f'{self.matricula.aluno} — {self.atribuicao.disciplina}: {self.valor}'
