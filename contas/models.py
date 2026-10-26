from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Perfil(models.TextChoices):
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
    DIRECCAO = 'DIRECCAO', 'Direcção'
    SECRETARIA = 'SECRETARIA', 'Secretaria'
    FINANCEIRO = 'FINANCEIRO', 'Financeiro'
    PROFESSOR = 'PROFESSOR', 'Professor'
    ALUNO = 'ALUNO', 'Aluno'
    ENCARREGADO = 'ENCARREGADO', 'Encarregado de educação'


class Utilizador(AbstractUser):
    """Conta de acesso ao sistema (tabela utilizadores)."""

    perfil = models.CharField(max_length=20, choices=Perfil.choices)
    tentativas_falhadas = models.PositiveSmallIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'utilizadores'
        verbose_name = 'utilizador'
        verbose_name_plural = 'utilizadores'

    def esta_bloqueado(self):
        """RN12: a conta está bloqueada até à data indicada."""
        return bool(self.bloqueado_ate and self.bloqueado_ate > timezone.now())

    def registar_falha(self):
        """RN12: após N falhas seguidas, bloqueia a conta durante M minutos."""
        self.tentativas_falhadas += 1
        if self.tentativas_falhadas >= settings.MAX_TENTATIVAS_LOGIN:
            self.bloqueado_ate = timezone.now() + timedelta(
                minutes=settings.MINUTOS_BLOQUEIO)
            self.tentativas_falhadas = 0
        self.save(update_fields=['tentativas_falhadas', 'bloqueado_ate'])

    def registar_sucesso(self):
        self.tentativas_falhadas = 0
        self.bloqueado_ate = None
        self.save(update_fields=['tentativas_falhadas', 'bloqueado_ate'])

    def desactivar(self):
        """RN11: os utilizadores não são eliminados, apenas desactivados."""
        self.is_active = False
        self.save(update_fields=['is_active'])

    def tem_perfil(self, *perfis):
        return self.is_superuser or self.perfil in perfis
