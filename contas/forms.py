from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label='Nome de utilizador', max_length=150)
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)
