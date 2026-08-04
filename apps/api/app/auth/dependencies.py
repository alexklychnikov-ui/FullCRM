from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.service import AuthenticatedUser, get_user_profile_by_id
from app.auth.tokens import ACCESS_TOKEN_TYPE, decode_token
from app.config import Settings
from app.db.session import get_db_session


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def current_access_payload(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    token = request.cookies.get(settings.auth_access_cookie_name)

    if not token:
        raise_unauthorized()

    payload = decode_token(settings, token, ACCESS_TOKEN_TYPE)

    if payload is None:
        raise_unauthorized()

    return payload


def current_user(
    payload: dict[str, Any] = Depends(current_access_payload),
    session: Session = Depends(get_db_session),
) -> AuthenticatedUser:
    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        raise_unauthorized()

    user = get_user_profile_by_id(session, user_id)

    if user is None or not user.is_active:
        raise_unauthorized()

    return user


def require_permission(permission: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    def dependency(user: AuthenticatedUser = Depends(current_user)) -> AuthenticatedUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return dependency


def require_role(role: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    def dependency(user: AuthenticatedUser = Depends(current_user)) -> AuthenticatedUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )

        return user

    return dependency


def require_module(module_key: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    def dependency(user: AuthenticatedUser = Depends(current_user)) -> AuthenticatedUser:
        if not user.has_module(module_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Module is disabled",
            )

        return user

    return dependency


def raise_unauthorized() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
