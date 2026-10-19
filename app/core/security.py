"""Argon2id para senhas e JWT HS256 para autenticação."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData

# Mantido para compatibilidade com os testes existentes; configuração permite apenas HS256.
ALGORITHM = "HS256"

password_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_secret_key() -> str:
    key = get_settings().secret_key
    if len(key.encode("utf-8")) < 32:
        raise RuntimeError("Configure SECRET_KEY com pelo menos 32 bytes aleatórios.")
    return key


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, get_secret_key(), algorithm=settings.algorithm)


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = jwt.decode(
            token,
            get_secret_key(),
            algorithms=[get_settings().algorithm],
            options={"require": ["sub", "exp", "iat"]},
        )
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub.isdecimal() or int(sub) <= 0:
            raise credentials_exception()
        token_data = TokenData(user_id=int(sub))
    except (InvalidTokenError, ValueError):
        raise credentials_exception() from None

    user = db.get(User, token_data.user_id)
    if user is None or not user.is_active:
        raise credentials_exception()
    return user
