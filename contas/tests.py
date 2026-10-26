from django.test import TestCase
from django.urls import reverse

from .models import Perfil, Utilizador


class BloqueioContaTests(TestCase):
    """TU01 — RN12: bloqueio após 5 tentativas falhadas."""

    def setUp(self):
        self.u = Utilizador.objects.create_user(
            'prof1', password='Senha#2026', perfil=Perfil.PROFESSOR)

    def test_bloqueia_apos_cinco_falhas(self):
        for _ in range(5):
            self.u.registar_falha()
        self.u.refresh_from_db()
        self.assertTrue(self.u.esta_bloqueado())

    def test_quatro_falhas_nao_bloqueiam(self):
        for _ in range(4):
            self.u.registar_falha()
        self.u.refresh_from_db()
        self.assertFalse(self.u.esta_bloqueado())

    def test_senha_guardada_com_bcrypt(self):
        """RNF03: a senha é guardada como hash bcrypt."""
        self.assertTrue(self.u.password.startswith('bcrypt_sha256$'))


class LoginViewTests(TestCase):
    """TI01 — RF02 e RN12 através da tela de login."""

    def setUp(self):
        Utilizador.objects.create_user('sec1', password='Senha#2026',
                                       perfil=Perfil.SECRETARIA)

    def test_login_correcto_abre_painel(self):
        r = self.client.post(reverse('login'),
                             {'username': 'sec1', 'password': 'Senha#2026'})
        self.assertRedirects(r, reverse('painel'))

    def test_conta_bloqueada_recusa_senha_correcta(self):
        for _ in range(5):
            self.client.post(reverse('login'),
                             {'username': 'sec1', 'password': 'errada'})
        r = self.client.post(reverse('login'),
                             {'username': 'sec1', 'password': 'Senha#2026'})
        self.assertContains(r, 'Conta bloqueada')
