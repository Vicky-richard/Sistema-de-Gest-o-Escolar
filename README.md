# Sistema de Gestão Escolar — Colégio Shalom

Protótipo desenvolvido no âmbito do trabalho prático de Engenharia de Software
(Instituto Superior Dom Bosco).

## Tecnologias
Python 3.12 · Django 5.2 · SQL Server 2022 Express (mssql-django) · Bootstrap 5

## Executar (desenvolvimento, SQLite)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py carregar_dados_demo
    python manage.py runserver

## Executar com SQL Server
Definir as variáveis de ambiente `DB_ENGINE=mssql`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD` e `DB_HOST` antes de `migrate`.

## Testes e qualidade
    coverage run manage.py test && coverage report
    radon cc -s -a .
    flake8
