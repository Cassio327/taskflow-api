"""Configuração de ambiente e engine independentes do SQLite de produção."""

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.db.session import create_db_engine


def test_settings_default_database_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.database_url == "sqlite:///./taskflow.db"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30


def test_settings_environment_has_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./outro.db")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")
    settings = get_settings()
    assert settings.database_url == "sqlite:///./outro.db"
    assert settings.access_token_expire_minutes == 45


@pytest.mark.parametrize("algorithm,expiration", [("none", "30"), ("HS256", "0")])
def test_reject_insecure_algorithm_or_invalid_expiration(
    monkeypatch: pytest.MonkeyPatch, algorithm: str, expiration: str
) -> None:
    monkeypatch.setenv("ALGORITHM", algorithm)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", expiration)
    with pytest.raises(ValidationError):
        get_settings()


def test_sqlite_engine_enforces_foreign_keys() -> None:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    finally:
        engine.dispose()
