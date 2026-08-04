from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user, get_settings
from app.auth.passwords import verify_password
from app.auth.schemas import LoginRequest
from app.auth.service import AuthenticatedUser, get_user_profile_by_id
from app.auth.sessions import (
    create_auth_session,
    get_active_auth_session,
    revoke_active_auth_session,
    revoke_auth_session_by_token,
)
from app.auth.tokens import (
    REFRESH_TOKEN_POLICY,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    create_refresh_token_jti,
    decode_token,
)
from app.config import Settings
from app.db.models import User
from app.db.session import get_db_session


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    ensure_auth_configured(settings)
    matching_users = session.scalars(select(User).where(User.email == payload.email.strip().lower())).all()

    if len(matching_users) != 1:
        raise_invalid_credentials()

    db_user = matching_users[0]

    if not verify_password(payload.password, db_user.password_hash):
        raise_invalid_credentials()

    user = get_user_profile_by_id(session, db_user.id)

    if user is None or not user.is_active:
        raise_invalid_credentials()

    refresh_token_jti = create_refresh_token_jti()
    refresh_token = create_refresh_token(settings, user.id, user.organization_id, refresh_token_jti)
    create_auth_session(session, settings, user.id, user.organization_id, refresh_token, refresh_token_jti, request)
    session.commit()
    set_auth_cookies(response, settings, user, refresh_token)
    return user.to_profile()


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    refresh_token = request.cookies.get(settings.auth_refresh_cookie_name)

    if not refresh_token:
        raise_invalid_refresh()

    payload = decode_token(settings, refresh_token, REFRESH_TOKEN_TYPE)

    if payload is None:
        raise_invalid_refresh()

    try:
        user_id = UUID(str(payload["sub"]))
        organization_id = UUID(str(payload["org"]))
    except ValueError:
        raise_invalid_refresh()

    refresh_token_jti = str(payload["jti"])
    auth_session = get_active_auth_session(session, refresh_token, refresh_token_jti, user_id, organization_id)

    if auth_session is None:
        raise_invalid_refresh()

    user = get_user_profile_by_id(session, user_id)

    if user is None or not user.is_active:
        raise_invalid_refresh()

    next_refresh_token_jti = create_refresh_token_jti()
    next_refresh_token = create_refresh_token(settings, user.id, user.organization_id, next_refresh_token_jti)

    if not revoke_active_auth_session(
        session,
        auth_session.id,
        refresh_token,
        refresh_token_jti,
        user.id,
        user.organization_id,
    ):
        raise_invalid_refresh()

    create_auth_session(session, settings, user.id, user.organization_id, next_refresh_token, next_refresh_token_jti, request)
    session.commit()
    response.set_cookie(
        key=settings.auth_access_cookie_name,
        value=create_access_token(settings, user.id, user.organization_id),
        max_age=settings.jwt_access_ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=next_refresh_token,
        max_age=settings.auth_cookie_max_age_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    profile = user.to_profile()
    profile["refreshTokenPolicy"] = REFRESH_TOKEN_POLICY
    return profile


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    refresh_token = request.cookies.get(settings.auth_refresh_cookie_name)

    if refresh_token:
        revoke_auth_session_by_token(session, refresh_token)
        session.commit()

    clear_auth_cookies(response, settings)
    return {"status": "ok"}


@router.get("/me")
def me(user: AuthenticatedUser = Depends(current_user)) -> dict[str, object]:
    return user.to_profile()


def set_auth_cookies(response: Response, settings: Settings, user: AuthenticatedUser, refresh_token: str) -> None:
    access_token = create_access_token(settings, user.id, user.organization_id)

    response.set_cookie(
        key=settings.auth_access_cookie_name,
        value=access_token,
        max_age=settings.jwt_access_ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        max_age=settings.auth_cookie_max_age_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    for cookie_name in (settings.auth_access_cookie_name, settings.auth_refresh_cookie_name):
        response.delete_cookie(
            key=cookie_name,
            httponly=True,
            secure=settings.auth_cookie_secure,
            samesite=settings.auth_cookie_samesite,
        )


def raise_invalid_credentials() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )


def raise_invalid_refresh() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )


def ensure_auth_configured(settings: Settings) -> None:
    try:
        settings.require_jwt_secret()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth is not configured",
        )
