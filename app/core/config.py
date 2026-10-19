"""Configuração única da aplicação, baseada em variáveis de ambiente."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora POSTGRES_PASSWORD, usada apenas pelo Compose
    )

    database_url: str = "sqlite:///./taskflow.db"
    secret_key: str = ""  # sem chave insegura padrão: a API falha ao iniciar
    algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)


def get_settings() -> Settings:
    # Não fazemos cache para facilitar testes e respeitar alterações de ambiente.
    return Settings()
