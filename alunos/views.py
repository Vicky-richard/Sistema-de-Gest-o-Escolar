from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from contas.models import Perfil
from contas.permissoes import perfil_requerido

from .forms import AlunoForm, MatriculaForm
from .models import Aluno


@perfil_requerido(Perfil.SECRETARIA, Perfil.ADMINISTRADOR)
def lista_alunos(request):
    alunos = Aluno.objects.filter(activo=True).prefetch_related(
        'matriculas__turma')
    return render(request, 'alunos/lista.html', {'alunos': alunos})


@perfil_requerido(Perfil.SECRETARIA, Perfil.ADMINISTRADOR)
def registar_aluno(request):
    """RF05 + RF06: regista o aluno e a matrícula numa só operação."""
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
