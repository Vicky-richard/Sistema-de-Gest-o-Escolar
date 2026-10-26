"""Carrega dados fictícios para demonstração do protótipo."""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from academico.models import Atribuicao, Disciplina, Professor
from alunos.models import Aluno, AlunoEncarregado, Encarregado, Matricula
from avaliacao import services
from contas.models import Perfil, Utilizador
from gestao_escolar.dados_teste import SENHA, criar_estrutura, criar_utilizador

ALUNOS = [('Carlos Sitoe', [14, 12.5, 15]), ('Elsa Macuácua', [9, 8.5, 10]),
          ('Hélio Nhantumbo', [16, 17, 15.5]), ('Inês Cumbe', [6.5, 7, 8]),
          ('Jorge Mabunda', [11, 10, 12])]


class Command(BaseCommand):
    help = 'Carrega dados fictícios de demonstração (senha de todos: %s)' % SENHA

    @transaction.atomic
    def handle(self, *args, **opts):
        if Utilizador.objects.filter(username='director').exists():
            self.stdout.write('Os dados de demonstração já existem.')
            return
        Utilizador.objects.create_superuser('admin', password=SENHA,
                                            perfil=Perfil.ADMINISTRADOR)
        d = criar_estrutura()
        sec = criar_utilizador('secretaria', Perfil.SECRETARIA, first_name='Lúcia')
        criar_utilizador('director', Perfil.DIRECCAO, first_name='Paulo',
                         last_name='Chissano')
        u_prof2 = criar_utilizador('prof.portugues', Perfil.PROFESSOR,
                                   first_name='Rui', last_name='Bila')
        portugues = Atribuicao.objects.create(
            turma=d['turma'], disciplina=Disciplina.objects.create(nome='Português'),
            professor=Professor.objects.create(utilizador=u_prof2, nome='Rui Bila'))
        u_enc = criar_utilizador('encarregado', Perfil.ENCARREGADO,
                                 first_name='Rosa', last_name='Sitoe')
        enc = Encarregado.objects.create(utilizador=u_enc, nome='Rosa Sitoe',
                                         telefone='84 000 0000')
        for i, (nome, notas) in enumerate(ALUNOS):
            u = criar_utilizador('aluno' if i == 0 else f'aluno{i}', Perfil.ALUNO,
                                 first_name=nome.split()[0])
            a = Aluno.objects.create(utilizador=u, nome=nome,
                                     data_nascimento=date(2012, 1 + i, 10))
            m = Matricula.objects.create(aluno=a, ano_lectivo=d['ano'],
                                         turma=d['turma'], tipo='Nova',
                                         registado_por=sec, estado='Confirmada')
            if i == 0:
                AlunoEncarregado.objects.create(aluno=a, encarregado=enc,
                                                parentesco='Mãe')
            for t, valor in enumerate(notas[:2], start=1):
                services.lancar_nota(d['u_prof'], d['atribuicao'], m, t,
                                     Decimal(str(valor)))
                services.lancar_nota(u_prof2, portugues, m, t,
                                     Decimal(str(min(20, valor + 1))))
        self.stdout.write(self.style.SUCCESS(
            'Dados carregados. Utilizadores: admin, director, secretaria, '
            'prof.matematica, prof.portugues, aluno, encarregado (senha %s)' % SENHA))
