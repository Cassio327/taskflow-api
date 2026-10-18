# TaskFlow API

[![CI - TaskFlow API](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml)

API REST para gerenciamento de tarefas com **FastAPI, SQLAlchemy, Pydantic, SQLite, JWT e Argon2id**. Cada usuário possui suas próprias tarefas, protegidas por autenticação.

## Requisitos e instalação

Python 3.11 recomendado (3.10+).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configure a chave secreta antes de iniciar a API:

```bash
printf 'SECRET_KEY=%s\n' "$(openssl rand -hex 32)" > .env
uvicorn app.main:app --reload
```

O arquivo `.env` é ignorado pelo Git. **Nunca envie a chave secreta para o repositório.** A API falhará na inicialização se a chave não estiver configurada ou for curta demais. Em produção, configure-a por variáveis de ambiente do provedor e utilize HTTPS.

API local: `http://127.0.0.1:8000/` — Swagger: `http://127.0.0.1:8000/docs`.

### Atenção: bancos SQLite das etapas anteriores

**`Base.metadata.create_all()` não altera tabelas já existentes.** O schema da Etapa 4 exige `user_id` obrigatório nas tarefas; o banco da Etapa 3 não possui essa coluna, nem usuários aos quais associar tarefas antigas.

Em um **ambiente de desenvolvimento**, se você já tem `taskflow.db`, faça backup antes de iniciar a Etapa 4:

```bash
# Feche o servidor antes.
if [ -f taskflow.db ]; then cp taskflow.db "taskflow-backup-$(date +%Y%m%d-%H%M%S).sqlite3"; fi
# Depois de confirmar o backup, remova apenas o banco de desenvolvimento antigo:
rm -f taskflow.db
```

Ao iniciar a API, um banco novo será criado com as tabelas `users` e `tasks`. **Não execute a remoção em dados importantes ou em produção.** Para preservar tarefas existentes, é necessária uma migração planejada (Alembic), com definição de propriedade dos registros antigos. Por segurança, a API identifica e rejeita o schema antigo em vez de utilizá-lo silenciosamente.

## Autenticação

| Método | Endpoint | Descrição | Autenticação |
| --- | --- | --- | --- |
| POST | `/auth/register` | Criar usuário | Não |
| POST | `/auth/token` | Login e JWT | Não |
| GET | `/` | Status da API | Não |
| GET | `/healthcheck` | Healthcheck | Não |
| POST | `/tasks` | Criar tarefa | Bearer JWT |
| GET | `/tasks` | Listar e filtrar suas tarefas | Bearer JWT |
| GET | `/tasks/{task_id}` | Consultar sua tarefa | Bearer JWT |
| PUT | `/tasks/{task_id}` | Alterar sua tarefa | Bearer JWT |
| DELETE | `/tasks/{task_id}` | Excluir sua tarefa | Bearer JWT |

### 1. Registrar um usuário

`POST /auth/register` com JSON:

```json
{"email": "pessoa@example.com", "password": "UmaSenhaForte123!"}
```

Retorna `201`, id, e-mail, status e data de criação (nunca a senha ou hash). E-mail já existente retorna `409`.

### 2. Efetuar login

`POST /auth/token` recebe **formulário `application/x-www-form-urlencoded`**, e não JSON. Use o e-mail no campo **`username`** e a senha no campo **`password`**:

```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -d 'username=pessoa@example.com' \
  -d 'password=UmaSenhaForte123!'
```

O retorno é `{"access_token": "...", "token_type": "bearer"}`. O JWT expira em 30 minutos. Tokens inválidos ou ausentes retornam `401`.

### 3. Usar o token no Swagger

Abra `/docs`, clique em **Authorize** e preencha os campos `username` (e-mail) e `password`. O Swagger executa o login e utiliza o token Bearer nas rotas protegidas. Alternativamente, envie o cabeçalho HTTP `Authorization: Bearer SEU_TOKEN`.

Exemplo de criação de tarefa:

```json
{"title": "Estudar FastAPI", "description": "Implementar login", "priority": "alta"}
```

Prioridades válidas: `baixa`, `media`, `alta`. A lista aceita `?completed=true` e `?priority=alta`. O usuário autenticado só pode ver ou modificar tarefas próprias. O acesso a um ID inexistente ou pertencente a outra pessoa retorna **404**, sem revelar sua existência. O campo `user_id` é definido pelo servidor a partir do token, nunca pelo cliente.

## Testes e integração contínua

```bash
python -m pytest -q
```

Os testes usam SQLite em memória e uma chave de **teste**, isolados do banco e das credenciais reais. O GitHub Actions executa o Pytest automaticamente em `push` e `pull_request` nas branches configuradas. Confira os resultados em [Actions](https://github.com/Cassio327/taskflow-api/actions).

## Estrutura

- `app/api/routes/`: endpoints de autenticação, tarefas e saúde
- `app/core/security.py`: hash Argon2id, JWT e dependência de usuário autenticado
- `app/models/`: modelos SQLAlchemy User e Task
- `app/schemas/`: schemas Pydantic para usuários, tarefas e tokens
- `app/services/`: lógica de registro, autenticação e CRUD
- `app/db/`: conexão e sessões do SQLite
- `tests/`: testes de autenticação, isolamento, CRUD e saúde

## Status do projeto

- [x] Etapa 1 — Estrutura da API FastAPI
- [x] Etapa 2 — CRUD com SQLAlchemy e Pytest
- [x] Etapa 3 — CI com GitHub Actions
- [x] Etapa 4 — Autenticação JWT, hash de senhas e isolamento por usuário

**Próximos passos antes de produção:** migração Alembic, rate limiting para login, políticas de recuperação de senha, gerenciamento/rotação de chaves JWT, HTTPS, armazenamento externo do banco e observabilidade.
