from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[Session, None, None]:
        with test_session() as db:
            yield db

    monkeypatch.setattr("app.main.engine", test_engine)
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()


def test_create_task_with_defaults(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "  Estudar FastAPI  "})

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Estudar FastAPI"
    assert body["description"] is None
    assert body["priority"] == "media"
    assert body["completed"] is False
    assert body["created_at"]


def test_create_and_get_task(client: TestClient) -> None:
    created = client.post(
        "/tasks", json={"title": "Programar", "description": "Praticar CRUD", "priority": "alta"}
    ).json()

    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_list_and_filter_tasks(client: TestClient) -> None:
    client.post("/tasks", json={"title": "A", "priority": "alta"})
    client.post("/tasks", json={"title": "B", "priority": "baixa", "completed": True})
    client.post("/tasks", json={"title": "C", "priority": "alta", "completed": True})

    assert len(client.get("/tasks").json()) == 3
    assert [t["title"] for t in client.get("/tasks?completed=true").json()] == ["B", "C"]
    assert [t["title"] for t in client.get("/tasks?priority=alta").json()] == ["A", "C"]
    assert [t["title"] for t in client.get("/tasks?completed=true&priority=alta").json()] == ["C"]


def test_update_task_partial_and_clear_description(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "Inicial", "description": "Antiga"}).json()
    task_id = created["id"]

    updated = client.put(f"/tasks/{task_id}", json={"completed": True, "priority": "alta"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "Inicial"
    assert updated.json()["completed"] is True
    assert updated.json()["priority"] == "alta"

    cleared = client.put(f"/tasks/{task_id}", json={"description": None})
    assert cleared.status_code == 200
    assert cleared.json()["description"] is None


def test_delete_task(client: TestClient) -> None:
    task_id = client.post("/tasks", json={"title": "Excluir"}).json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/tasks/{task_id}").status_code == 404


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_task_returns_404(client: TestClient, method: str) -> None:
    if method == "put":
        response = client.put("/tasks/999", json={"title": "Novo título"})
    else:
        response = getattr(client, method)("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada."


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": "   "}, {"title": "Estudar", "priority": "urgente"}],
)
def test_invalid_task_creation_returns_422(client: TestClient, payload: dict) -> None:
    assert client.post("/tasks", json=payload).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [{"title": None}, {"priority": None}, {"completed": None}, {"title": "   "}],
)
def test_invalid_update_returns_422(client: TestClient, payload: dict) -> None:
    task_id = client.post("/tasks", json={"title": "Válida"}).json()["id"]
    assert client.put(f"/tasks/{task_id}", json=payload).status_code == 422


def test_invalid_query_priority_returns_422(client: TestClient) -> None:
    assert client.get("/tasks?priority=urgente").status_code == 422


def test_isolated_database_per_test(client: TestClient) -> None:
    assert client.get("/tasks").json() == []
