from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from contas.models import Perfil

from .forms import AlunoForm, MatriculaForm
from .models import Aluno


def _exigir_secretaria(user):
    if not user.tem_perfil(Perfil.SECRETARIA, Perfil.ADMINISTRADOR):
        raise PermissionDenied


@login_required
def lista_alunos(request):
    _exigir_secretaria(request.user)
    alunos = Aluno.objects.filter(activo=True).prefetch_related(
        'matriculas__turma')
    return render(request, 'alunos/lista.html', {'alunos': alunos})


@login_required
def registar_aluno(request):
    """RF05 + RF06: regista o aluno e a matrícula numa só operação."""
    _exigir_secretaria(request.user)
    form_a = AlunoForm(request.POST or None, prefix='a')
    form_m = MatriculaForm(request.POST or None, prefix='m')
    if request.method == 'POST' and form_a.is_valid() and form_m.is_valid():
        try:
            with transaction.atomic():
                aluno = form_a.save()
                matricula = form_m.save(commit=False)
                matricula.aluno = aluno
                matricula.registado_por = request.user
                matricula.full_clean()
                matricula.save()
        except IntegrityError:
            messages.error(request, 'O aluno já tem matrícula neste ano lectivo.')
        else:
            messages.success(request, f'Aluno {aluno} registado e matriculado '
                                      f'(matrícula pendente de pagamento).')
            return redirect('lista_alunos')
    return render(request, 'alunos/registar.html',
                  {'form_a': form_a, 'form_m': form_m})
