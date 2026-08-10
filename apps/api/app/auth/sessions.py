from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import AuthSession


def hash_refresh_token(refresh_token: str) -> str:
    return sha256(refresh_token.encode("utf-8")).hexdigest()


def create_auth_session(
    session: Session,
    settings: Settings,
    user_id: UUID,
    organization_id: UUID,
    refresh_token: str,
    refresh_token_jti: str,
    request: Request,
    now: datetime | None = None,
) -> AuthSession:
    issued_at = now or datetime.now(UTC)
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    auth_session = AuthSession(
        user_id=user_id,
        organization_id=organization_id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        refresh_token_jti=refresh_token_jti,
        expires_at=issued_at + timedelta(seconds=settings.jwt_refresh_ttl_seconds),
        user_agent=user_agent[:255] if user_agent else None,
        ip_address=client_host[:64] if client_host else None,
    )
    session.add(auth_session)
    return auth_session


def get_active_auth_session(
    session: Session,
    refresh_token: str,
    refresh_token_jti: str,
    user_id: UUID,
    organization_id: UUID,
    now: datetime | None = None,
) -> AuthSession | None:
    checked_at = now or datetime.now(UTC)
    return session.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == hash_refresh_token(refresh_token),
            AuthSession.refresh_token_jti == refresh_token_jti,
            AuthSession.user_id == user_id,
            AuthSession.organization_id == organization_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > checked_at,
        )
    )


def revoke_auth_session(auth_session: AuthSession, now: datetime | None = None) -> None:
    auth_session.revoked_at = now or datetime.now(UTC)


def revoke_active_auth_session(
    session: Session,
    auth_session_id: UUID,
    refresh_token: str,
    refresh_token_jti: str,
    user_id: UUID,
    organization_id: UUID,
    now: datetime | None = None,
) -> bool:
    revoked_at = now or datetime.now(UTC)
    result = session.execute(
        update(AuthSession)
        .where(
            AuthSession.id == auth_session_id,
            AuthSession.refresh_token_hash == hash_refresh_token(refresh_token),
            AuthSession.refresh_token_jti == refresh_token_jti,
            AuthSession.user_id == user_id,
            AuthSession.organization_id == organization_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > revoked_at,
        )
        .values(revoked_at=revoked_at)
    )
    return result.rowcount == 1


def revoke_auth_session_by_token(
    session: Session,
    refresh_token: str,
    now: datetime | None = None,
) -> bool:
    auth_session = session.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == hash_refresh_token(refresh_token),
            AuthSession.revoked_at.is_(None),
        )
    )

    if auth_session is None:
        return False

    revoke_auth_session(auth_session, now)
    return True


def revoke_all_user_sessions(
    session: Session,
    user_id: UUID,
    organization_id: UUID,
    now: datetime | None = None,
) -> int:
    revoked_at = now or datetime.now(UTC)
    result = session.execute(
        update(AuthSession)
        .where(
            AuthSession.user_id == user_id,
            AuthSession.organization_id == organization_id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )
    return int(result.rowcount or 0)
