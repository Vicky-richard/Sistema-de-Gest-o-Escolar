"""Dados de base reutilizados pelos testes e pelo comando de demonstração."""
from datetime import date

from academico.models import AnoLectivo, Atribuicao, Classe, Disciplina, Professor, Turma
from contas.models import Perfil, Utilizador

SENHA = 'Senha#2026'


def criar_utilizador(username, perfil, **extra):
    return Utilizador.objects.create_user(username, password=SENHA,
                                          perfil=perfil, **extra)


def criar_estrutura():
    """Cria ano lectivo, classe, turma, disciplina, professor e atribuição."""
    ano = AnoLectivo.objects.create(designacao='2026', activo=True,
                                    data_inicio=date(2026, 2, 1),
                                    data_fim=date(2026, 11, 30))
    classe = Classe.objects.create(nome='8.ª Classe', ordem=8)
    turma = Turma.objects.create(ano_lectivo=ano, classe=classe, nome='A',
                                 turno='Manhã')
    disciplina = Disciplina.objects.create(nome='Matemática')
    u_prof = criar_utilizador('prof.matematica', Perfil.PROFESSOR,
                              first_name='Ana', last_name='Mondlane')
    professor = Professor.objects.create(utilizador=u_prof, nome='Ana Mondlane')
    atribuicao = Atribuicao.objects.create(turma=turma, disciplina=disciplina,
                                           professor=professor)
    return {'ano': ano, 'classe': classe, 'turma': turma,
            'disciplina': disciplina, 'professor': professor,
            'u_prof': u_prof, 'atribuicao': atribuicao}
