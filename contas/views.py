from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from academico.models import Atribuicao, Turma

from .forms import LoginForm
from .models import Perfil, Utilizador


def entrar(request):
    """RF02: autenticação com nome de utilizador e senha (com RN12)."""
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        conta = Utilizador.objects.filter(username=username).first()
        if conta and conta.esta_bloqueado():
            messages.error(request, 'Conta bloqueada temporariamente. '
                                    'Tente novamente mais tarde.')
            return render(request, 'contas/login.html', {'form': form})
        utilizador = authenticate(request, username=username,
                                  password=form.cleaned_data['password'])
        if utilizador:
            utilizador.registar_sucesso()
            login(request, utilizador)
            return redirect('painel')
        if conta:
            conta.registar_falha()
        messages.error(request, 'Nome de utilizador ou senha incorrectos.')
    return render(request, 'contas/login.html', {'form': form})


@login_required
def painel(request):
    contexto = {}
    if request.user.perfil == Perfil.PROFESSOR:
        contexto['atribuicoes'] = Atribuicao.objects.filter(
            professor__utilizador=request.user).select_related('turma', 'disciplina')
    if request.user.perfil in (Perfil.DIRECCAO, Perfil.SECRETARIA):
        contexto['turmas'] = Turma.objects.filter(ano_lectivo__activo=True)
    return render(request, 'contas/painel.html', contexto)
