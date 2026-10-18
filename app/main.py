from fastapi import FastAPI

from app.api.routes import health

app = FastAPI(
    title="TaskFlow API",
    description="API REST para gerenciamento de tarefas.",
    version="0.1.0",
)

app.include_router(health.router, tags=["Status"])
