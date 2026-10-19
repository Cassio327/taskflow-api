# TaskFlow API

[![CI - TaskFlow API](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Cassio327/taskflow-api/actions/workflows/ci.yml)

API REST multiusuário para gerenciamento de tarefas com **FastAPI, SQLAlchemy, Pydantic, JWT, Argon2id, PostgreSQL, Alembic, Docker e Pytest**. Cada usuário pode consultar e modificar apenas suas próprias tarefas.

## Requisitos

- Para usar Docker: Docker Engine e plugin Docker Compose (`docker compose`).
- Sem Docker: Python 3.11, com suporte a SQLite ou PostgreSQL instalado separadamente.
- `openssl` para gerar credenciais aleatórias para desenvolvimento local.

## Executar com Docker Compose (recomendado)

Na pasta do projeto, execute:

```bash
cp -n .env.example .env
sed -i "s/^SECRET_KEY=$/SECRET_KEY=$(openssl rand -hex 32)/" .env
sed -i "s/^POSTGRES_PASSWORD=$/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" .env

docker compose up --build -d
docker compose ps
docker compose logs -f api
```

Abra <http://127.0.0.1:8000/docs> para acessar o Swagger ou <http://127.0.0.1:8000/healthcheck> para verificar o status da API.

**Como funciona:** `docker-compose.yml` sobe o PostgreSQL 17 com o serviço `db` e a aplicação FastAPI com o serviço `api`. O Compose aguarda o banco ficar saudável (`pg_isready`) antes de iniciar a API. Em seguida, `entrypoint.sh` executa `alembic upgrade head` e só então inicia o Uvicorn. Uma migração que falhe impede o servidor de iniciar.

A aplicação roda com usuário não privilegiado dentro de uma imagem Python 3.11-slim de dois estágios. O serviço PostgreSQL não publica a porta `5432` no host; a API fica disponível somente na interface local `127.0.0.1:8000` (não diretamente na internet).

O arquivo `.env` é local e ignorado pelo Git e pela imagem Docker. O Compose usa `SECRET_KEY`, `POSTGRES_PASSWORD`, `ALGORITHM` e `ACCESS_TOKEN_EXPIRE_MINUTES`. A URL de conexão **dentro do container** usa o hostname `db` e é passada por variável de ambiente; a `DATABASE_URL` do `.env` serve para o Python executado diretamente no Ubuntu. Gere `POSTGRES_PASSWORD` como valor hexadecimal, evitando caracteres que precisem de codificação especial na URL SQLAlchemy.

### Operações do Docker

```bash
# Subir/recriar containers em segundo plano
docker compose up --build -d

# Acompanhar logs
docker compose logs -f api
docker compose logs -f db

# Verificar serviços
docker compose ps

# Executar testes (SQLite em memória para isolamento)
docker compose exec api python -m pytest -q

# Confirmar versão de migração no PostgreSQL
docker compose exec api alembic current

# Verificar conexão real com PostgreSQL
docker compose exec api python -c "from sqlalchemy import text; from app.db.session import engine; c = engine.connect(); print(c.execute(text('SELECT 1')).scalar_one()); c.close()"

# Parar e remover os containers, preservando os dados
docker compose down
```

**Importante:** nunca use `docker compose down -v` se quiser preservar as tarefas e os usuários: `-v` remove o volume persistente `postgres_data`. Os dados continuam após `docker compose down` e um novo `docker compose up`.

Se você já executava **somente o PostgreSQL** com o Compose da Etapa 5, use `docker compose down` antes de subir o arquivo novo para parar o container antigo. O volume `postgres_data` é preservado, desde que mantenha a mesma pasta/nome de projeto do Compose. Se o volume tiver sido inicializado anteriormente, **não troque** sua senha apenas editando `.env`: altere-a também no próprio PostgreSQL.

### Primeiro teste da API com PostgreSQL

1. Abra o Swagger em <http://127.0.0.1:8000/docs>.
2. Cadastre-se em `POST /auth/register` com `{"email":"usuario@example.com","password":"UmaSenhaForte123!"}`.
3. Clique em **Authorize**, use o e-mail no campo `username` e a senha no campo `password`.
4. Crie uma tarefa em `POST /tasks` e liste-a em `GET /tasks`.
5. Cadastre outro usuário e verifique que ele não consegue visualizar a primeira tarefa.

Isso valida o fluxo de autenticação e persistência no PostgreSQL de verdade. Os testes automatizados com SQLite não substituem esse teste fim a fim.

## Executar sem Docker (SQLite)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp -n .env.example .env
sed -i "s/^SECRET_KEY=$/SECRET_KEY=$(openssl rand -hex 32)/" .env
alembic upgrade head
uvicorn app.main:app --reload
```

O valor padrão `DATABASE_URL=sqlite:///./taskflow.db` é adequado para desenvolvimento local. Para executar o servidor fora do Docker **contra o PostgreSQL** do Compose, é necessário expor a porta do serviço `db` em `127.0.0.1:5432` (configuração opcional) e alterar a URL local para usar `127.0.0.1`, pois o hostname `db` só é resolvido dentro da rede Docker.

## Configurações

| Variável | Descrição | Valor padrão |
| --- | --- | --- |
| `DATABASE_URL` | URL SQLAlchemy da conexão quando usado fora do Compose | `sqlite:///./taskflow.db` |
| `SECRET_KEY` | Chave para assinatura JWT | Obrigatória, pelo menos 32 bytes aleatórios |
| `ALGORITHM` | Algoritmo de JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do token JWT | `30` |
| `POSTGRES_PASSWORD` | Credencial inicial do banco no Compose | Obrigatória para Docker |

**Segurança:** nunca publique `.env`, tokens ou senhas. Use credenciais exclusivas por ambiente. Para produção, utilize HTTPS, gerenciador de segredos, backups e estratégia de migração sem executar simultaneamente múltiplas instâncias migradoras.

## Alembic — controle das migrações

O Alembic usa `Base.metadata`, os modelos `User` e `Task` e a URL configurada para aplicar revisões incrementais. A primeira revisão (`0001_initial`) cria tabelas, índices e a chave estrangeira `tasks.user_id`.

```bash
# Execute sem Docker depois de ativar .venv e configurar DATABASE_URL
alembic upgrade head
alembic current
alembic check
alembic revision --autogenerate -m "nova alteracao"

# Ou execute dentro do container que já está rodando
docker compose exec api alembic current
docker compose exec api alembic check
```

Revise migrações autogeradas antes de aplicá-las. **Em bancos já existentes**, `0001_initial` não deve recriar tabelas existentes: faça backup e planeje a migração adequada; não elimine dados importantes. O script de entrada executa automaticamente as migrações ao inicializar a API no Compose.

## Testes e CI

```bash
python -m pytest -q
```

Os testes existentes utilizam SQLite em memória e dependências substituídas para não alterar o banco real. O GitHub Actions roda a suíte de Pytest e valida o Alembic em um banco SQLite temporário. Testes de integração completos com PostgreSQL ainda devem ser realizados no ambiente Docker.

## Endpoints

| Método | Endpoint | Autenticação | Função |
| --- | --- | --- | --- |
| GET | `/` | Não | Status da API |
| GET | `/healthcheck` | Não | Healthcheck |
| POST | `/auth/register` | Não | Cadastro de usuários |
| POST | `/auth/token` | Não | Login OAuth2 e retorno JWT |
| POST | `/tasks` | Bearer JWT | Criar tarefa própria |
| GET | `/tasks` | Bearer JWT | Listar e filtrar tarefas próprias |
| GET | `/tasks/{task_id}` | Bearer JWT | Buscar tarefa própria |
| PUT | `/tasks/{task_id}` | Bearer JWT | Atualizar tarefa própria |
| DELETE | `/tasks/{task_id}` | Bearer JWT | Remover tarefa própria |

## Estrutura do projeto

```text
Dockerfile
.dockerignore
entrypoint.sh
docker-compose.yml
.env.example
alembic.ini
alembic/
  env.py
  versions/0001_initial_migration.py
app/
  api/routes/
  core/
  db/
  models/
  schemas/
  services/
tests/
.github/workflows/ci.yml
```

## Status do projeto

- [x] Etapa 1 — Estrutura inicial com FastAPI.
- [x] Etapa 2 — CRUD de tarefas com SQLAlchemy.
- [x] Etapa 3 — Pytest e GitHub Actions.
- [x] Etapa 4 — JWT, Argon2id e isolamento por usuário.
- [x] Etapa 5 — PostgreSQL, variáveis de ambiente e Alembic.
- [x] Etapa 6 — Dockerização da API e orquestração com PostgreSQL.

**Próxima etapa:** disponibilizar a API em um ambiente de hospedagem com HTTPS e política de backups. Antes do deploy, testar o Compose com PostgreSQL real e avaliar como gerenciar migrações em produção.
