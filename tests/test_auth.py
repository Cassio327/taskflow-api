from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import ALGORITHM, get_secret_key, verify_password
from app.db.session import get_db
from app.models.user import User


def test_register_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "  Pessoa@Example.com ", "password": "SenhaForte123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "pessoa@example.com"
    assert data["is_active"] is True
    assert data["created_at"]
    assert "password" not in data
    assert "hashed_password" not in data

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.scalar(select(User).where(User.email == "pessoa@example.com"))
        assert user.hashed_password != "SenhaForte123!"
        assert user.hashed_password.startswith("$argon2id$")
        assert verify_password("SenhaForte123!", user.hashed_password)
    finally:
        db.close()


def test_duplicate_email_case_insensitive(client: TestClient) -> None:
    data = {"email": "pessoa@example.com", "password": "SenhaForte123!"}
    assert client.post("/auth/register", json=data).status_code == 201
    assert client.post("/auth/register", json={**data, "email": "PESSOA@EXAMPLE.COM"}).status_code == 409


def test_login_and_use_access_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/auth/token", data={"username": "PESSOA@EXAMPLE.COM", "password": "SenhaForte123!"}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert client.get("/tasks", headers=auth_headers).status_code == 200


@pytest.mark.parametrize(
    "username,password",
    [("pessoa@example.com", "senha-errada"), ("desconhecido@example.com", "SenhaForte123!")],
)
def test_login_invalid_credentials(
    client: TestClient, auth_headers: dict[str, str], username: str, password: str
) -> None:
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "nao-e-email", "password": "SenhaForte123!"},
        {"email": "pessoa@example.com", "password": "curta"},
    ],
)
def test_invalid_registration(client: TestClient, payload: dict) -> None:
    assert client.post("/auth/register", json=payload).status_code == 422


def test_invalid_and_expired_tokens(client: TestClient, auth_headers: dict[str, str]) -> None:
    expired = jwt.encode(
        {
            "sub": "1",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        get_secret_key(),
        algorithm=ALGORITHM,
    )
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "iat": datetime.now(timezone.utc)},
        "secret-that-is-not-the-real-key-longer-than-32-bytes",
        algorithm=ALGORITHM,
    )
    for token in ("invalid.token", expired, forged):
        response = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_inactive_user_is_denied(client: TestClient, auth_headers: dict[str, str]) -> None:
    get_session = client.app.dependency_overrides[get_db]
    session = next(get_session())
    try:
        user = session.scalar(select(User).where(User.email == "pessoa@example.com"))
        user.is_active = False
        session.commit()
    finally:
        session.close()
    assert client.get("/tasks", headers=auth_headers).status_code == 401
    assert client.post(
        "/auth/token", data={"username": "pessoa@example.com", "password": "SenhaForte123!"}
    ).status_code == 401


def test_missing_secret_key_causes_startup_failure(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    from app.main import app
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        with TestClient(app):
            pass
