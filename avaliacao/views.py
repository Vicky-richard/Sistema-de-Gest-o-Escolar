from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from academico.models import Atribuicao, Turma
from alunos.models import Aluno
from contas.models import Perfil
from contas.permissoes import perfil_requerido

from . import services
from .models import Nota


def _validar_submissao(post, matriculas):
    """Lê as notas submetidas; devolve (válidas, valores digitados, erros)."""
    validas, valores, erros = {}, {}, {}
    for m in matriculas:
        texto = post.get(f'nota_{m.pk}', '').strip()
        if not texto:
            continue
        valores[m.pk] = texto
        try:
            validas[m] = services.converter_nota(texto)
        except ValidationError as e:
            erros[m.pk] = e.messages[0]
    return validas, valores, erros


@perfil_requerido(Perfil.PROFESSOR)
def lancar_notas(request, atribuicao_id, trimestre):
    """RF14: o professor lança as notas de uma turma/disciplina/trimestre."""
    atribuicao = get_object_or_404(Atribuicao.objects.select_related(
        'turma', 'disciplina', 'professor'), pk=atribuicao_id)
    if atribuicao.professor.utilizador_id != request.user.pk:          # RN08
        raise PermissionDenied
    pauta = services.obter_pauta(atribuicao.turma, trimestre)
    matriculas = atribuicao.turma.matriculas.select_related('aluno').order_by(
        'aluno__nome')
    valores = {n.matricula_id: n.valor for n in Nota.objects.filter(
        atribuicao=atribuicao, trimestre=trimestre)}
    erros = {}
    if request.method == 'POST' and not pauta.esta_fechada():
        validas, digitados, erros = _validar_submissao(request.POST, matriculas)
        valores.update(digitados)
        if not erros:
            for m, valor in validas.items():
                services.lancar_nota(request.user, atribuicao, m, trimestre, valor)
            messages.success(request, f'{len(validas)} nota(s) guardada(s).')
            return redirect('lancar_notas', atribuicao_id, trimestre)
        messages.error(request, 'Existem notas inválidas. Corrija os campos assinalados.')
    linhas = [(m, valores.get(m.pk, ''), erros.get(m.pk)) for m in matriculas]
    return render(request, 'avaliacao/lancar_notas.html', {
        'atribuicao': atribuicao, 'trimestre': trimestre, 'pauta': pauta,
        'linhas': linhas})


@perfil_requerido(Perfil.DIRECCAO, Perfil.SECRETARIA, Perfil.PROFESSOR)
def ver_pauta(request, turma_id, trimestre):
    """RF16: pauta da turma no trimestre."""
    turma = get_object_or_404(Turma, pk=turma_id)
    pauta = services.obter_pauta(turma, trimestre)
    atribuicoes = list(turma.atribuicao_set.select_related('disciplina')
                       .order_by('disciplina__nome'))
    notas = {(n.matricula_id, n.atribuicao_id): n.valor for n in Nota.objects.filter(
        atribuicao__turma=turma, trimestre=trimestre)}
    linhas = [(m, [notas.get((m.pk, a.pk)) for a in atribuicoes])
              for m in turma.matriculas.select_related('aluno').order_by('aluno__nome')]
    return render(request, 'avaliacao/pauta.html', {
        'turma': turma, 'pauta': pauta, 'atribuicoes': atribuicoes,
        'linhas': linhas, 'em_falta': services.notas_em_falta(pauta),
        'pode_fechar': request.user.tem_perfil(Perfil.DIRECCAO)})


@perfil_requerido(Perfil.DIRECCAO)
@require_POST
def fechar_pauta(request, turma_id, trimestre):
    """RF18: fechar e validar a pauta."""
    pauta = services.obter_pauta(get_object_or_404(Turma, pk=turma_id), trimestre)
    try:
        services.fechar_pauta(pauta, request.user)
    except ValidationError as e:
        messages.error(request, f'Não é possível fechar a pauta: {e.messages[0]}')
    else:
        messages.success(request, 'Pauta fechada e validada.')
    return redirect('ver_pauta', turma_id, trimestre)


def _boletim(aluno):
    """Notas por disciplina, média e resultado (RN04) do ano corrente."""
    linhas = []
    matricula = aluno.matriculas.order_by('-ano_lectivo__data_inicio').first()
    if not matricula:
        return None, linhas
    for a in matricula.turma.atribuicao_set.select_related('disciplina'):
        por_trim = {n.trimestre: n.valor for n in matricula.notas.filter(atribuicao=a)}
        media, resultado = services.calcular_resultado(list(por_trim.values()))
        linhas.append((a.disciplina, [por_trim.get(t) for t in (1, 2, 3)],
                       media, resultado))
    return matricula, linhas


@perfil_requerido(Perfil.ALUNO, Perfil.ENCARREGADO)
def consultar_notas(request):
    """RF17 e RN09: o aluno vê as suas notas; o encarregado as dos educandos."""
    user = request.user
    if user.perfil == Perfil.ALUNO:
        alunos = Aluno.objects.filter(utilizador=user)
    else:
        alunos = Aluno.objects.filter(encarregados__utilizador=user)
    boletins = [(a, *_boletim(a)) for a in alunos]
    return render(request, 'avaliacao/consultar_notas.html', {'boletins': boletins})
