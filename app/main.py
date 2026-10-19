"""Aplicação FastAPI: migrations são executadas pelo Alembic, não no startup."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, health, tasks
from app.core.security import get_secret_key


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_secret_key()  # impede iniciar sem chave segura
    # Execute `alembic upgrade head` antes de iniciar a API.
    yield


app = FastAPI(
    title="TaskFlow API",
    description="API REST de tarefas com JWT, PostgreSQL e migrações Alembic.",
    version="0.5.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["Status"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tarefas"])
