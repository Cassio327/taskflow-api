# TaskFlow API

[![CI - TaskFlow API](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml)

API REST para gerenciamento de tarefas feita com FastAPI, SQLAlchemy, Pydantic e SQLite. O projeto utiliza uma arquitetura em camadas para separar rotas HTTP, validação, persistência e regras de negócio.

## Instalação e execução

Requer Python 3.10 ou superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

API em <http://127.0.0.1:8000/>; documentação Swagger em <http://127.0.0.1:8000/docs>.

O arquivo `taskflow.db` será criado automaticamente na pasta raiz ao iniciar o servidor.

## Endpoints

| Método | Endpoint | Descrição |
| --- | --- | --- |
| GET | `/` | Verificar se a aplicação está online |
| GET | `/healthcheck` | Healthcheck básico |
| POST | `/tasks` | Criar tarefa (201) |
| GET | `/tasks` | Listar e filtrar por `completed` e `priority` |
| GET | `/tasks/{task_id}` | Buscar uma tarefa |
| PUT | `/tasks/{task_id}` | Atualizar campos fornecidos |
| DELETE | `/tasks/{task_id}` | Excluir tarefa (204, sem corpo) |

### Exemplo de criação

```json
{
  "title": "Estudar FastAPI",
  "description": "Implementar API REST",
  "priority": "alta"
}
```

Prioridades válidas: `baixa`, `media`, `alta`. Valores padrão: `priority=media`, `completed=false`. Para concluir uma tarefa sem excluí-la, use `PUT /tasks/{task_id}` com `{"completed": true}`.

## Testes

```bash
python -m pytest -q
```

Os testes de tarefas utilizam um SQLite em memória com sessões isoladas e não acessam o arquivo local de produção.

## Estrutura

- `app/api/routes/`: endpoints HTTP
- `app/schemas/`: validação de entrada/saída (Pydantic)
- `app/models/`: classes ORM (SQLAlchemy)
- `app/db/`: conexão e sessão de banco
- `app/services/`: operações CRUD
- `tests/`: testes automatizados

> Nota: `Base.metadata.create_all()` é suficiente para esta etapa local. Para evoluir o schema de um banco existente em produção, adicione migrações com Alembic.

## Status do Projeto

- [x] Etapa 1 — Estrutura inicial e FastAPI.
- [x] Etapa 2 — CRUD de tarefas com SQLite e Pytest.
- [x] Etapa 3 — Integração contínua com GitHub Actions.

O workflow de CI executa os testes automaticamente em Python 3.11 em cada push e Pull Request para as branches configuradas. Confira os resultados em [GitHub Actions](https://github.com/Cassio327/taskflow-api/actions).
