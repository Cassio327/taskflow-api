"""Smoke test da migração Alembic em um SQLite temporário."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_initial_migration_upgrade_check_and_downgrade(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        inspector = inspect(engine)
        assert {"users", "tasks", "alembic_version"}.issubset(inspector.get_table_names())
        assert "user_id" in {col["name"] for col in inspector.get_columns("tasks")}
        assert any(fk["referred_table"] == "users" for fk in inspector.get_foreign_keys("tasks"))
        assert any(index["name"] == "ix_users_email" for index in inspector.get_indexes("users"))
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001_initial"
    finally:
        engine.dispose()

    command.check(config)  # sem alterações pendentes em relação aos modelos ORM
    command.downgrade(config, "base")
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        assert "users" not in inspect(engine).get_table_names()
        assert "tasks" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()
