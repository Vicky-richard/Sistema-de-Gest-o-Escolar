from django.conf import settings
from django.db import models


class AnoLectivo(models.Model):
    designacao = models.CharField(max_length=20, unique=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    activo = models.BooleanField(default=False)

    class Meta:
        db_table = 'anos_lectivos'
        verbose_name = 'ano lectivo'
        verbose_name_plural = 'anos lectivos'
        constraints = [models.CheckConstraint(
            condition=models.Q(data_fim__gt=models.F('data_inicio')),
            name='ck_ano_datas')]

    def __str__(self):
        return self.designacao


class Classe(models.Model):
    nome = models.CharField(max_length=30, unique=True)
    ordem = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        db_table = 'classes'
        ordering = ['ordem']

    def __str__(self):
        return self.nome


class Disciplina(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = 'disciplinas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Turma(models.Model):
    TURNOS = [('Manhã', 'Manhã'), ('Tarde', 'Tarde'), ('Noite', 'Noite')]
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.PROTECT)
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT)
    nome = models.CharField(max_length=20)
    turno = models.CharField(max_length=15, choices=TURNOS)

    class Meta:
        db_table = 'turmas'
        constraints = [models.UniqueConstraint(
            fields=['ano_lectivo', 'classe', 'nome'], name='uq_turma')]

    def __str__(self):
        return f'{self.classe} {self.nome} ({self.ano_lectivo})'


class Professor(models.Model):
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL,
                                      on_delete=models.PROTECT)
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'professores'
        verbose_name_plural = 'professores'

    def __str__(self):
        return self.nome


class Atribuicao(models.Model):
    """RF11: professor responsável por uma disciplina numa turma."""
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT)
    professor = models.ForeignKey(Professor, on_delete=models.PROTECT)

    class Meta:
        db_table = 'atribuicoes'
        verbose_name = 'atribuição'
        verbose_name_plural = 'atribuições'
        constraints = [models.UniqueConstraint(
            fields=['turma', 'disciplina'], name='uq_atribuicao')]

    def __str__(self):
        return f'{self.disciplina} — {self.turma} — {self.professor}'
