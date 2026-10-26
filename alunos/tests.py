from datetime import date

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from contas.models import Perfil
from gestao_escolar.dados_teste import criar_estrutura, criar_utilizador

from .models import Aluno, Matricula


class MatriculaUnicaTests(TestCase):
    """TU02 — RN01: uma só matrícula por aluno e ano lectivo."""

    def setUp(self):
        self.d = criar_estrutura()
        self.sec = criar_utilizador('sec', Perfil.SECRETARIA)
        self.aluno = Aluno.objects.create(nome='João Cossa',
                                          data_nascimento=date(2012, 5, 3))

    def _matricular(self):
        return Matricula.objects.create(aluno=self.aluno, ano_lectivo=self.d['ano'],
                                        turma=self.d['turma'], tipo='Nova',
                                        registado_por=self.sec)

    def test_segunda_matricula_no_mesmo_ano_e_recusada(self):
        self._matricular()
        with self.assertRaises(IntegrityError):
            self._matricular()

    def test_matricula_comeca_pendente(self):
        """RN02: a matrícula só é confirmada após o pagamento."""
        self.assertEqual(self._matricular().estado, 'Pendente')


class RegistarAlunoViewTests(TestCase):
    """TI02 — RF05/RF06: registo de aluno e matrícula pela Secretaria."""

    def setUp(self):
        self.d = criar_estrutura()
        self.sec = criar_utilizador('sec', Perfil.SECRETARIA)

    def _dados(self):
        return {'a-nome': 'Maria Langa', 'a-data_nascimento': '2012-03-10',
                'm-ano_lectivo': self.d['ano'].pk, 'm-turma': self.d['turma'].pk,
                'm-tipo': 'Nova'}

    def test_secretaria_regista_aluno_e_matricula(self):
        self.client.force_login(self.sec)
        r = self.client.post(reverse('registar_aluno'), self._dados())
        self.assertRedirects(r, reverse('lista_alunos'))
        self.assertEqual(Matricula.objects.get().aluno.nome, 'Maria Langa')

    def test_professor_nao_pode_registar_alunos(self):
        """RNF04: acesso controlado por perfil."""
        self.client.force_login(self.d['u_prof'])
        r = self.client.post(reverse('registar_aluno'), self._dados())
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Aluno.objects.exists())
