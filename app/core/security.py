import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Parâmetros mínimos recomendados pela OWASP para Argon2id: 19 MiB, 2 iterações, 1 thread.
password_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "")
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
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM)


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
            algorithms=[ALGORITHM],
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
