"""Shared FastAPI dependencies for HITL service."""

from collections.abc import AsyncGenerator

import structlog
from config import settings
from db.session import get_session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if not getattr(settings, "auth_enabled", True):
        return

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        import base64 as _b64
        import json as _json

        _raw = credentials.credentials.split(".")[1]
        _raw += "=" * (4 - len(_raw) % 4)
        _audience = _json.loads(_b64.urlsafe_b64decode(_raw)).get("aud")
    except Exception:
        _audience = None

    try:
        jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=_audience,
            options={"verify_aud": False},
        )
    except JWTError as exc:
        logger.warning("jwt_decode_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc
