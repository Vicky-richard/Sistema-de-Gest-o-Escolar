from django import forms

from .models import Aluno, Matricula


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'data_nascimento', 'doc_identificacao', 'morada',
                  'telefone']
        widgets = {'data_nascimento': forms.DateInput(attrs={'type': 'date'})}


class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ['ano_lectivo', 'turma', 'tipo']
