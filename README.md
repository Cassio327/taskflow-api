# TaskFlow API

[![CI - TaskFlow API](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml)

API REST multiusuário para gerenciamento de tarefas, com **FastAPI, SQLAlchemy, JWT, Argon2id, PostgreSQL/SQLite, Alembic e testes Pytest**. Cada pessoa só acessa suas próprias tarefas.

## Requisitos

- Python 3.11 recomendado (mínimo: Python 3.10).
- PostgreSQL 17 via Docker (opcional). SQLite continua disponível para desenvolvimento e testes.
- `openssl` para gerar a chave secreta da autenticação.

## Instalação e configuração local

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp -n .env.example .env
sed -i "s/^SECRET_KEY=$/SECRET_KEY=$(openssl rand -hex 32)/" .env
```

A aplicação lê automaticamente as variáveis do `.env` por meio de `app/core/config.py` (`pydantic-settings`). Variáveis exportadas no sistema têm prioridade sobre os valores no `.env`.

| Variável | Finalidade | Padrão seguro |
| --- | --- | --- |
| `DATABASE_URL` | URL SQLAlchemy de conexão | `sqlite:///./taskflow.db` |
| `SECRET_KEY` | Assinatura dos JWT | **Obrigatória**: mínimo de 32 bytes aleatórios, sem valor padrão |
| `ALGORITHM` | Algoritmo aceito para JWT | `HS256` (único permitido) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duração do acesso | `30` |
| `POSTGRES_PASSWORD` | Senha inicial do Postgres Docker | Obrigatória **somente** ao usar Compose |

**Nunca publique seu `.env`**. Ele é ignorado pelo Git. Para produção, configure os segredos no ambiente do serviço de hospedagem, use HTTPS e mantenha credenciais fortes.

### Opção A — SQLite local (sem Docker)

Deixe `DATABASE_URL=sqlite:///./taskflow.db` no `.env` e rode:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

### Opção B — PostgreSQL com Docker Compose

O arquivo `docker-compose.yml` cria um Postgres 17 com volume persistente, `healthcheck` e porta exposta somente em `127.0.0.1` no computador local.

```bash
# Na pasta raiz do projeto, após criar o .env e configurar SECRET_KEY:
POSTGRES_PASSWORD=$(openssl rand -hex 16)
sed -i "s/^POSTGRES_PASSWORD=.*$/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://taskflow:$POSTGRES_PASSWORD@127.0.0.1:5432/taskflow|" .env

docker compose up -d
# Verifique se o banco está pronto: docker compose ps
alembic upgrade head
uvicorn app.main:app --reload
```

Execute a configuração de senha do PostgreSQL apenas na primeira inicialização do volume. Esses comandos utilizam uma senha hexadecimal para evitar caracteres que precisariam ser codificados na URL. Se usar senha com `@`, `:` ou `/`, faça URL-encoding na `DATABASE_URL`.

> Alterar `POSTGRES_PASSWORD` após o banco já ter sido inicializado não altera a senha do usuário existente no volume Docker. Gerencie a alteração dentro do próprio PostgreSQL se necessário.

## Migrações com Alembic

O schema é versionado no diretório `alembic/versions/`. Na Etapa 5, a migração `0001_initial` cria `users`, `tasks`, seus índices e a chave estrangeira `tasks.user_id`.

```bash
alembic upgrade head                           # aplicar todas as revisões pendentes
alembic current                                # mostrar versão atual no banco
alembic history                                # histórico de revisões
alembic check                                  # conferir se modelos e schema divergem
alembic revision --autogenerate -m "nova mudança"  # gerar uma proposta de migração
```

**Revise qualquer migração autogerada antes de executá-la.** O Alembic compara `Base.metadata` dos modelos importados no `alembic/env.py` com o banco definido por `DATABASE_URL`. A aplicação **não chama mais `create_all()` ao iniciar**; execute `alembic upgrade head` antes de subir o servidor.

### Banco SQLite já existente das Etapas 3 ou 4

A migração `0001_initial` é destinada a **bancos vazios**. Se você já usa `taskflow.db`, fazer `alembic upgrade head` nesse banco com tabelas existentes pode falhar com `table already exists`. **Não apague o banco se houver dados importantes.**

Opção segura para desenvolvimento: faça backup e aponte o `.env` para um arquivo novo, sem destruir o antigo:

```bash
cp taskflow.db "taskflow-backup-$(date +%Y%m%d-%H%M%S).sqlite3"
sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:///./taskflow-v5.db|' .env
alembic upgrade head
```

Se precisar **preservar e migrar os dados antigos**, planeje uma migração específica. Um banco da Etapa 3 sequer possui usuários para associar às tarefas; não se deve atribuir proprietários automaticamente. Para um banco da Etapa 4 cujo esquema tenha sido **confirmado idêntico** à migração inicial, `alembic stamp head` pode apenas registrar a revisão existente — **não** altera nem valida a estrutura do banco por si só. Faça backup e confira o schema antes de usar `stamp`.

## Executar e testar

Após aplicar as migrações:

```bash
uvicorn app.main:app --reload
```

API local: http://127.0.0.1:8000/; documentação Swagger: http://127.0.0.1:8000/docs.

```bash
python -m pytest -q
```

Os testes usam SQLite em memória e isolam o banco de dados do ambiente configurado. O CI executa testes, aplica a migração inicial a um SQLite temporário e roda `alembic check`. Não é necessário iniciar Docker para a suíte de testes.

## Endpoints

| Método | Endpoint | Autenticação | Descrição |
| --- | --- | --- | --- |
| GET | `/` | Não | Status da aplicação |
| GET | `/healthcheck` | Não | Healthcheck |
| POST | `/auth/register` | Não | Criar usuário |
| POST | `/auth/token` | Não | Login OAuth2 e JWT |
| POST | `/tasks` | JWT | Criar tarefa do usuário atual |
| GET | `/tasks` | JWT | Listar tarefas próprias (filtros `completed` e `priority`) |
| GET | `/tasks/{task_id}` | JWT | Buscar sua tarefa |
| PUT | `/tasks/{task_id}` | JWT | Atualizar sua tarefa |
| DELETE | `/tasks/{task_id}` | JWT | Excluir sua tarefa |

### Autenticação

1. Cadastre-se em `POST /auth/register` com JSON: `{"email":"pessoa@example.com","password":"UmaSenhaForte123!"}`.
2. Faça login em `POST /auth/token` com **formulário**, usando e-mail no campo `username` e senha no campo `password`.
3. Em `/docs`, clique em **Authorize** para informar credenciais. O Swagger obterá o token e adicionará automaticamente `Authorization: Bearer ...` nas rotas protegidas.

Senhas são armazenadas como hash **Argon2id**. Tokens JWT usam exclusivamente **HS256** e expiram após o tempo configurado. O usuário é identificado pelo JWT, nunca pelo `user_id` informado pelo cliente. Acesso a tarefa de outro usuário retorna 404.

## Estrutura principal

```text
app/
  api/routes/       # auth, tasks e health
  core/config.py    # variáveis de ambiente validadas
  core/security.py  # Argon2id e JWT
  db/session.py     # engine PostgreSQL/SQLite e sessão
  models/           # tabelas ORM
  schemas/          # modelos de entrada e saída
  services/         # regras de negócio
alembic/
  env.py
  versions/0001_initial_migration.py
.github/workflows/ci.yml
README.md
requirements.txt
docker-compose.yml
.env.example
```

## Status do projeto

- [x] Etapa 1 — Estrutura inicial com FastAPI.
- [x] Etapa 2 — CRUD de tarefas com SQLAlchemy.
- [x] Etapa 3 — Testes e CI com GitHub Actions.
- [x] Etapa 4 — Autenticação JWT e isolamento por usuário.
- [x] Etapa 5 — PostgreSQL, configuração por ambiente e migrações Alembic.

Próximas melhorias possíveis: Dockerfile para a API, deploy com HTTPS, rate limiting de login, análise estática, backups e observabilidade. O PostgreSQL em execução real deve ser validado no ambiente com Docker; o CI usa SQLite para ser leve.
