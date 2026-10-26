"""Camada de serviços: regras de negócio da avaliação (RN03–RN08)."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from auditoria.models import LogAuditoria
from contas.models import Perfil

from .models import Nota, Pauta, validar_valor_nota

LIMITE_FALTAS = Decimal('25')  # RN05 (%)


class Resultado:
    APROVADO = 'Aprovado'
    RECURSO = 'Recurso'
    REPROVADO = 'Reprovado'
    REPROVADO_POR_FALTAS = 'Reprovado por faltas'


def converter_nota(texto):
    """Converte o texto introduzido numa nota válida (RN03)."""
    try:
        valor = Decimal(str(texto).replace(',', '.').strip())
    except InvalidOperation:
        raise ValidationError('Valor não numérico.')
    validar_valor_nota(valor)
    return valor


def calcular_resultado(notas_trimestrais, percentagem_faltas=Decimal('0')):
    """RN04 e RN05: devolve (média, resultado) de uma disciplina."""
    if percentagem_faltas > LIMITE_FALTAS:
        return None, Resultado.REPROVADO_POR_FALTAS
    if not notas_trimestrais:
        return None, None
    media = (sum(notas_trimestrais) / len(notas_trimestrais)).quantize(
        Decimal('0.1'), rounding=ROUND_HALF_UP)
    if media >= 10:
        return media, Resultado.APROVADO
    if media >= 7:
        return media, Resultado.RECURSO
    return media, Resultado.REPROVADO


def obter_pauta(turma, trimestre):
    pauta, _ = Pauta.objects.get_or_create(turma=turma, trimestre=trimestre)
    return pauta


def lancar_nota(utilizador, atribuicao, matricula, trimestre, valor):
    """RF14: lança ou corrige uma nota, respeitando RN03, RN07 e RN08."""
    if atribuicao.professor.utilizador_id != utilizador.pk:      # RN08
        raise PermissionDenied('Professor não atribuído a esta turma/disciplina.')
    if obter_pauta(atribuicao.turma, trimestre).esta_fechada():  # RN07
        raise ValidationError('A pauta está fechada; só a Direcção pode alterar.')
    validar_valor_nota(valor)
    nota, criada = Nota.objects.get_or_create(
        matricula=matricula, atribuicao=atribuicao, trimestre=trimestre,
        defaults={'valor': valor, 'lancado_por': utilizador})
    if not criada and nota.valor != valor:
        nota.valor = valor
        nota.alterado_por = utilizador
        nota.save()
    return nota


def notas_em_falta(pauta):
    """Número de notas por lançar na pauta (alunos × disciplinas)."""
    turma = pauta.turma
    matriculas = turma.matriculas.exclude(estado='Anulada').count()
    disciplinas = turma.atribuicao_set.count()
    lancadas = Nota.objects.filter(atribuicao__turma=turma,
                                   trimestre=pauta.trimestre).count()
    return matriculas * disciplinas - lancadas


@transaction.atomic
def fechar_pauta(pauta, utilizador):
    """RF18: a Direcção fecha e valida a pauta (ver especificação formal)."""
    if not utilizador.tem_perfil(Perfil.DIRECCAO):
        raise PermissionDenied('Só a Direcção pode fechar pautas.')
    if pauta.esta_fechada():
        raise ValidationError('A pauta já está fechada.')
    if notas_em_falta(pauta) > 0:
        raise ValidationError('Existem notas por lançar.')
    pauta.estado = Pauta.Estado.FECHADA
    pauta.fechada_por = utilizador
    pauta.fechada_em = timezone.now()
    pauta.save()
    LogAuditoria.objects.create(utilizador=utilizador, accao='FECHO_PAUTA',
                                tabela='pautas', id_registo=pauta.pk,
                                valor_anterior='Aberta', valor_novo='Fechada')
    return pauta


def alterar_nota_apos_fecho(nota, novo_valor, justificacao, utilizador):
    """RN07: alteração pela Direcção, com justificação e registo em log."""
    if not utilizador.tem_perfil(Perfil.DIRECCAO):
        raise PermissionDenied('Só a Direcção pode alterar notas após o fecho.')
    if not justificacao.strip():
        raise ValidationError('A justificação é obrigatória.')
    validar_valor_nota(novo_valor)
    nota.valor = novo_valor
    nota.alterado_por = utilizador
    nota.justificacao = f' (justificação: {justificacao.strip()})'
    nota.save()
    return nota
