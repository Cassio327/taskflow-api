from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect

from app.api.routes import auth, health, tasks
from app.core.security import get_secret_key
from app.db.base import Base
from app.db.session import engine
from app.models import task as task_model
from app.models import user as user_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_secret_key()  # Falha na inicialização se SECRET_KEY não estiver configurada.
    inspector = inspect(engine)
    if "tasks" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("tasks")}
        if "user_id" not in columns:
            raise RuntimeError(
                "Banco SQLite da etapa anterior detectado: faça backup e use um banco novo "
                "ou aplique uma migração planejada antes de iniciar a Etapa 4."
            )
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TaskFlow API",
    description="API REST de tarefas com autenticação JWT e isolamento por usuário.",
    version="0.4.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["Status"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tarefas"])
