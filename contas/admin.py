from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilizador


@admin.register(Utilizador)
class UtilizadorAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Perfil e segurança', {'fields': ('perfil', 'tentativas_falhadas',
                                           'bloqueado_ate')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('perfil',)}),)
    list_display = ('username', 'first_name', 'last_name', 'perfil', 'is_active')
    list_filter = ('perfil', 'is_active')
