"""Controlo de acesso por perfil (RNF04), reutilizado por todas as apps."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def perfil_requerido(*perfis):
    """Só deixa passar utilizadores autenticados com um dos perfis indicados."""
    def decorador(view):
        @login_required
        @wraps(view)
        def envolvida(request, *args, **kwargs):
            if not request.user.tem_perfil(*perfis):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return envolvida
    return decorador
