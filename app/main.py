from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes import health, tasks
from app.db.base import Base
from app.db.session import engine
from app.models import task as task_model  # registra a tabela no metadata


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TaskFlow API",
    description="API REST para gerenciamento de tarefas.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["Status"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tarefas"])
