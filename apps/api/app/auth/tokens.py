from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import Settings


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
REFRESH_TOKEN_POLICY = "server_session_rotation"


def create_access_token(settings: Settings, user_id: UUID, organization_id: UUID) -> str:
    return create_token(
        settings=settings,
        user_id=user_id,
        organization_id=organization_id,
        token_type=ACCESS_TOKEN_TYPE,
        ttl_seconds=settings.jwt_access_ttl_seconds,
    )


def create_refresh_token(
    settings: Settings,
    user_id: UUID,
    organization_id: UUID,
    token_jti: str | None = None,
) -> str:
    return create_token(
        settings=settings,
        user_id=user_id,
        organization_id=organization_id,
        token_type=REFRESH_TOKEN_TYPE,
        ttl_seconds=settings.jwt_refresh_ttl_seconds,
        token_jti=token_jti,
    )


def create_token(
    settings: Settings,
    user_id: UUID,
    organization_id: UUID,
    token_type: str,
    ttl_seconds: int,
    token_jti: str | None = None,
) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "typ": token_type,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=ttl_seconds),
    }

    if token_jti is not None:
        payload["jti"] = token_jti

    return jwt.encode(payload, settings.require_jwt_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token_jti() -> str:
    return str(uuid4())


def decode_token(settings: Settings, token: str, expected_type: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.require_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except (ExpiredSignatureError, InvalidTokenError, RuntimeError):
        return None

    if payload.get("typ") != expected_type:
        return None

    if not payload.get("sub") or not payload.get("org"):
        return None

    if expected_type == REFRESH_TOKEN_TYPE and not payload.get("jti"):
        return None

    return payload
