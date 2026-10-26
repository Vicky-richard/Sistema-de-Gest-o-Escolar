from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from academico.models import AnoLectivo, Turma


class Aluno(models.Model):
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL, null=True,
                                      blank=True, on_delete=models.PROTECT)
    nome = models.CharField(max_length=120)
    data_nascimento = models.DateField()
    doc_identificacao = models.CharField(max_length=30, null=True, blank=True,
                                         unique=True)
    morada = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)
    encarregados = models.ManyToManyField('Encarregado',
                                          through='AlunoEncarregado')

    class Meta:
        db_table = 'alunos'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def desactivar(self):
        """RN11: desactivar em vez de eliminar."""
        self.activo = False
        self.save(update_fields=['activo'])


class Encarregado(models.Model):
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL, null=True,
                                      blank=True, on_delete=models.PROTECT)
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    class Meta:
        db_table = 'encarregados'

    def __str__(self):
        return self.nome


class AlunoEncarregado(models.Model):
    """RF07: associação N:M entre alunos e encarregados."""
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    encarregado = models.ForeignKey(Encarregado, on_delete=models.CASCADE)
    parentesco = models.CharField(max_length=30)

    class Meta:
        db_table = 'aluno_encarregado'
        constraints = [models.UniqueConstraint(
            fields=['aluno', 'encarregado'], name='pk_aluno_encarregado')]


class Matricula(models.Model):
    """RF06: matrícula ou renovação por ano lectivo."""

    class Tipo(models.TextChoices):
        NOVA = 'Nova'
        RENOVACAO = 'Renovação'
        TRANSFERENCIA = 'Transferência'

    class Estado(models.TextChoices):
        PENDENTE = 'Pendente'
        CONFIRMADA = 'Confirmada'
        ANULADA = 'Anulada'
        TRANSFERIDA = 'Transferida'

    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT,
                              related_name='matriculas')
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.PROTECT)
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT,
                              related_name='matriculas')
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    estado = models.CharField(max_length=15, choices=Estado.choices,
                              default=Estado.PENDENTE)
    data_registo = models.DateTimeField(auto_now_add=True)
    registado_por = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      on_delete=models.PROTECT)

    class Meta:
        db_table = 'matriculas'
        constraints = [models.UniqueConstraint(          # RN01
            fields=['aluno', 'ano_lectivo'], name='uq_matricula_ano')]

    def __str__(self):
        return f'{self.aluno} — {self.turma}'

    def clean(self):
        if self.turma_id and self.ano_lectivo_id and \
                self.turma.ano_lectivo_id != self.ano_lectivo_id:
            raise ValidationError('A turma não pertence ao ano lectivo indicado.')

    def confirmar(self):
        """RN02: confirmada após o pagamento da taxa (registado pelo Financeiro)."""
        self.estado = self.Estado.CONFIRMADA
        self.save(update_fields=['estado'])
