# TaskFlow API

API REST de gerenciamento de tarefas, construída com FastAPI e organizada em camadas.

## Tecnologias

Python 3.10+, FastAPI, SQLAlchemy, SQLite, Pytest e Git.

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse:

- API: http://127.0.0.1:8000/
- Healthcheck: http://127.0.0.1:8000/healthcheck
- Documentação interativa: http://127.0.0.1:8000/docs

## Testes

```bash
python -m pytest -q
```

## Organização

- `app/api/routes`: endpoints HTTP.
- `app/schemas`: validação de entrada e saída com Pydantic (próxima etapa).
- `app/models`: tabelas SQLAlchemy (próxima etapa).
- `app/db`: base e configuração de sessões do banco.
- `app/services`: regras de negócio (próxima etapa).
- `tests`: testes automatizados.

> **Etapa 1:** estrutura inicial, endpoints de status, configuração de banco e testes básicos. O CRUD de tarefas será desenvolvido na etapa 2.
