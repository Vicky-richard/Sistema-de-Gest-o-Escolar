from datetime import date
from decimal import Decimal as D

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from alunos.models import Aluno, AlunoEncarregado, Encarregado, Matricula
from auditoria.models import LogAuditoria
from contas.models import Perfil
from gestao_escolar.dados_teste import criar_estrutura, criar_utilizador

from . import services
from .models import Nota, Pauta
from .services import Resultado


# ---------------------------------------------------------------- unitários
class CalcularResultadoTests(SimpleTestCase):
    """TU03 — RN04 e RN05: cálculo da média e do resultado."""

    def test_media_igual_ou_superior_a_10_aprova(self):
        self.assertEqual(services.calcular_resultado([D('9.5'), D('10.5'), D('10')]),
                         (D('10.0'), Resultado.APROVADO))

    def test_media_entre_7_e_10_vai_a_recurso(self):
        self.assertEqual(services.calcular_resultado([D('8'), D('9')])[1],
                         Resultado.RECURSO)

    def test_media_inferior_a_7_reprova(self):
        self.assertEqual(services.calcular_resultado([D('5'), D('6.5')])[1],
                         Resultado.REPROVADO)

    def test_faltas_acima_de_25_por_cento_reprovam(self):
        self.assertEqual(services.calcular_resultado([D('18')], D('26'))[1],
                         Resultado.REPROVADO_POR_FALTAS)


class ConverterNotaTests(SimpleTestCase):
    """TU04 — RN03: escala de 0 a 20 com uma casa decimal."""

    def test_aceita_virgula_decimal(self):
        self.assertEqual(services.converter_nota('12,5'), D('12.5'))

    def test_recusa_valores_invalidos(self):
        for texto in ('21', '-1', '12.55', 'abc'):
            with self.subTest(texto=texto), self.assertRaises(ValidationError):
                services.converter_nota(texto)


# ------------------------------------------------------------- integração
class BaseAvaliacao(TestCase):
    def setUp(self):
        self.d = criar_estrutura()
        self.sec = criar_utilizador('sec', Perfil.SECRETARIA)
        self.dir = criar_utilizador('director', Perfil.DIRECCAO)
        self.alunos = []
        for nome in ('Carlos Sitoe', 'Elsa Macuácua'):
            a = Aluno.objects.create(nome=nome, data_nascimento=date(2012, 1, 1))
            Matricula.objects.create(aluno=a, ano_lectivo=self.d['ano'],
                                     turma=self.d['turma'], tipo='Nova',
                                     registado_por=self.sec)
            self.alunos.append(a)
        self.matriculas = list(Matricula.objects.order_by('aluno__nome'))

    def lancar_todas(self, valor=D('12')):
        for m in self.matriculas:
            services.lancar_nota(self.d['u_prof'], self.d['atribuicao'], m, 1, valor)


class LancarNotaServiceTests(BaseAvaliacao):
    """TI03 — RF14, RN08 e Observer de auditoria (RNF06)."""

    def test_alteracao_de_nota_e_registada_no_log(self):
        m = self.matriculas[0]
        services.lancar_nota(self.d['u_prof'], self.d['atribuicao'], m, 1, D('9'))
        services.lancar_nota(self.d['u_prof'], self.d['atribuicao'], m, 1, D('11'))
        log = LogAuditoria.objects.get(accao='ALTERAR_NOTA')
        self.assertEqual((log.valor_anterior, log.valor_novo), ('9.0', '11.0'))
        self.assertEqual(log.utilizador, self.d['u_prof'])

    def test_professor_nao_atribuido_e_recusado(self):
        outro = criar_utilizador('prof2', Perfil.PROFESSOR)
        with self.assertRaises(PermissionDenied):
            services.lancar_nota(outro, self.d['atribuicao'], self.matriculas[0], 1,
                                 D('10'))

    def test_aluno_de_outra_turma_e_recusado(self):
        """Pré-condição m.turma = a.turma (Capítulo VI)."""
        from academico.models import Turma
        outra = Turma.objects.create(ano_lectivo=self.d['ano'], classe=self.d['classe'],
                                     nome='B', turno='Tarde')
        m = self.matriculas[0]
        m.turma = outra
        m.save()
        with self.assertRaises(ValidationError):
            services.lancar_nota(self.d['u_prof'], self.d['atribuicao'], m, 1, D('10'))


class FecharPautaServiceTests(BaseAvaliacao):
    """TI04 — RF18 e RN07: fecho da pauta."""

    def setUp(self):
        super().setUp()
        self.pauta = services.obter_pauta(self.d['turma'], 1)

    def test_nao_fecha_com_notas_em_falta(self):
        services.lancar_nota(self.d['u_prof'], self.d['atribuicao'],
                             self.matriculas[0], 1, D('12'))
        with self.assertRaises(ValidationError):
            services.fechar_pauta(self.pauta, self.dir)

    def test_direccao_fecha_pauta_completa(self):
        self.lancar_todas()
        services.fechar_pauta(self.pauta, self.dir)
        self.pauta.refresh_from_db()
        self.assertEqual(self.pauta.estado, Pauta.Estado.FECHADA)
        self.assertTrue(LogAuditoria.objects.filter(accao='FECHO_PAUTA').exists())

    def test_professor_nao_pode_fechar(self):
        self.lancar_todas()
        with self.assertRaises(PermissionDenied):
            services.fechar_pauta(self.pauta, self.d['u_prof'])

    def test_apos_fecho_so_direccao_altera_com_justificacao(self):
        self.lancar_todas()
        services.fechar_pauta(self.pauta, self.dir)
        with self.assertRaises(ValidationError):
            services.lancar_nota(self.d['u_prof'], self.d['atribuicao'],
                                 self.matriculas[0], 1, D('15'))
        nota = Nota.objects.filter(matricula=self.matriculas[0]).get()
        services.alterar_nota_apos_fecho(nota, D('13'), 'Erro de transcrição', self.dir)
        log = LogAuditoria.objects.get(accao='ALTERAR_NOTA')
        self.assertIn('Erro de transcrição', log.valor_novo)
        self.assertEqual(log.utilizador, self.dir)


# ---------------------------------------------------- sistema / aceitação
class FluxoPautaSistemaTests(BaseAvaliacao):
    """TS01 — do lançamento das notas ao fecho da pauta, pelas telas."""

    def test_fluxo_completo(self):
        url = reverse('lancar_notas', args=[self.d['atribuicao'].pk, 1])
        self.client.force_login(self.d['u_prof'])
        dados = {f'nota_{m.pk}': '14,5' for m in self.matriculas}
        # 1. nota inválida é assinalada e nada é guardado
        r = self.client.post(url, {**dados, f'nota_{self.matriculas[0].pk}': '25'})
        self.assertContains(r, 'notas inválidas')
        self.assertFalse(Nota.objects.exists())
        # 2. notas válidas são guardadas
        self.client.post(url, dados)
        self.assertEqual(Nota.objects.count(), 2)
        # 3. a Direcção fecha a pauta
        self.client.force_login(self.dir)
        r = self.client.post(reverse('fechar_pauta', args=[self.d['turma'].pk, 1]),
                             follow=True)
        self.assertContains(r, 'Pauta fechada e validada')
        # 4. o professor já não consegue alterar as notas
        self.client.force_login(self.d['u_prof'])
        self.client.post(url, {f'nota_{self.matriculas[0].pk}': '5'})
        self.assertEqual(Nota.objects.get(matricula=self.matriculas[0]).valor, D('14.5'))


class ConsultaNotasSistemaTests(BaseAvaliacao):
    """TS02 — RF17 e RN09: cada utilizador só vê as notas que lhe competem."""

    def test_encarregado_ve_apenas_o_seu_educando(self):
        self.lancar_todas(D('15'))
        u_enc = criar_utilizador('enc', Perfil.ENCARREGADO)
        enc = Encarregado.objects.create(utilizador=u_enc, nome='Rosa Sitoe',
                                         telefone='840000000')
        AlunoEncarregado.objects.create(aluno=self.alunos[0], encarregado=enc,
                                        parentesco='Mãe')
        self.client.force_login(u_enc)
        r = self.client.get(reverse('consultar_notas'))
        self.assertContains(r, 'Carlos Sitoe')
        self.assertNotContains(r, 'Elsa Macuácua')

    def test_professor_nao_acede_a_consulta_de_aluno(self):
        self.client.force_login(self.d['u_prof'])
        self.assertEqual(self.client.get(reverse('consultar_notas')).status_code, 403)
