import pytest
from fastapi.testclient import TestClient


def test_create_task_with_defaults(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/tasks", json={"title": "  Estudar FastAPI  "}, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["user_id"] == 1
    assert body["title"] == "Estudar FastAPI"
    assert body["description"] is None
    assert body["priority"] == "media"
    assert body["completed"] is False
    assert body["created_at"]


def test_create_and_get_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/tasks",
        json={"title": "Programar", "description": "Praticar CRUD", "priority": "alta"},
        headers=auth_headers,
    ).json()
    response = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == created


def test_list_and_filter_tasks(client: TestClient, auth_headers: dict[str, str]) -> None:
    for data in (
        {"title": "A", "priority": "alta"},
        {"title": "B", "priority": "baixa", "completed": True},
        {"title": "C", "priority": "alta", "completed": True},
    ):
        client.post("/tasks", json=data, headers=auth_headers)

    def titles(path: str) -> list[str]:
        return [t["title"] for t in client.get(path, headers=auth_headers).json()]

    assert titles("/tasks") == ["A", "B", "C"]
    assert titles("/tasks?completed=true") == ["B", "C"]
    assert titles("/tasks?priority=alta") == ["A", "C"]
    assert titles("/tasks?completed=true&priority=alta") == ["C"]


def test_update_task_partial_and_clear_description(client: TestClient, auth_headers: dict[str, str]) -> None:
    task_id = client.post(
        "/tasks", json={"title": "Inicial", "description": "Antiga"}, headers=auth_headers
    ).json()["id"]

    updated = client.put(
        f"/tasks/{task_id}", json={"completed": True, "priority": "alta"}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Inicial"
    assert updated.json()["completed"] is True
    assert updated.json()["priority"] == "alta"

    cleared = client.put(f"/tasks/{task_id}", json={"description": None}, headers=auth_headers)
    assert cleared.status_code == 200
    assert cleared.json()["description"] is None


def test_delete_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    task_id = client.post("/tasks", json={"title": "Excluir"}, headers=auth_headers).json()["id"]
    response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/tasks/{task_id}", headers=auth_headers).status_code == 404


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_task_returns_404(client: TestClient, auth_headers: dict[str, str], method: str) -> None:
    if method == "put":
        response = client.put("/tasks/999", json={"title": "Novo título"}, headers=auth_headers)
    else:
        response = getattr(client, method)("/tasks/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada."


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": "   "}, {"title": "Estudar", "priority": "urgente"}],
)
def test_invalid_task_creation_returns_422(
    client: TestClient, auth_headers: dict[str, str], payload: dict
) -> None:
    assert client.post("/tasks", json=payload, headers=auth_headers).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [{"title": None}, {"priority": None}, {"completed": None}, {"title": "   "}],
)
def test_invalid_update_returns_422(client: TestClient, auth_headers: dict[str, str], payload: dict) -> None:
    task_id = client.post("/tasks", json={"title": "Válida"}, headers=auth_headers).json()["id"]
    assert client.put(f"/tasks/{task_id}", json=payload, headers=auth_headers).status_code == 422


def test_invalid_query_priority_returns_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/tasks?priority=urgente", headers=auth_headers).status_code == 422


def test_isolated_database_per_test(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/tasks", headers=auth_headers).json() == []


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_protected_routes_require_login(client: TestClient, method: str) -> None:
    path = "/tasks" if method in ("get", "post") else "/tasks/1"
    kwargs = {"json": {"title": "Teste"}} if method in ("post", "put") else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


def test_tasks_isolated_between_users(client: TestClient, auth_headers: dict[str, str]) -> None:
    alice = auth_headers
    task = client.post("/tasks", json={"title": "Tarefa da Alice"}, headers=alice).json()
    task_id = task["id"]

    client.post("/auth/register", json={"email": "bob@example.com", "password": "SenhaDoBob123!"})
    login = client.post(
        "/auth/token", data={"username": "bob@example.com", "password": "SenhaDoBob123!"}
    )
    assert login.status_code == 200
    bob = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get("/tasks", headers=bob).json() == []
    assert client.get(f"/tasks/{task_id}", headers=bob).status_code == 404
    assert client.put(
        f"/tasks/{task_id}", json={"title": "Tentativa de alteração"}, headers=bob
    ).status_code == 404
    assert client.delete(f"/tasks/{task_id}", headers=bob).status_code == 404

    response = client.post(
        "/tasks", json={"title": "Tarefa do Bob", "user_id": task["user_id"]}, headers=bob
    )
    assert response.status_code == 201
    assert response.json()["user_id"] != task["user_id"]
    assert [t["title"] for t in client.get("/tasks", headers=bob).json()] == ["Tarefa do Bob"]
    assert [t["title"] for t in client.get("/tasks", headers=alice).json()] == ["Tarefa da Alice"]
    assert client.get(f"/tasks/{task_id}", headers=alice).json()["title"] == "Tarefa da Alice"
