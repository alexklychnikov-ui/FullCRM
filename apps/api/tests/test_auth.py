from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth.dependencies import require_module, require_permission, require_role
from app.auth.passwords import hash_password
from app.auth.sessions import hash_refresh_token
from app.auth.service import AuthenticatedUser
from app.config import Settings
from app.db.models import AuthSession, User
from app.db.session import get_db_session
from app.main import create_app


@dataclass
class UserRecord:
    id: UUID
    password_hash: str


class FakeSession:
    def __init__(self, user: UserRecord | None) -> None:
        self.user = user
        self.auth_sessions: list[AuthSession] = []
        self.force_revoke_rowcount_zero = False
        self.last_active_auth_session: AuthSession | None = None

    def scalars(self, statement: object) -> "FakeScalarResult":
        if statement_entity(statement) is not User:
            return FakeScalarResult([])

        if self.user is None:
            return FakeScalarResult([])

        return FakeScalarResult([self.user])

    def scalar(self, statement: object) -> AuthSession | None:
        if statement_entity(statement) is not AuthSession:
            return None

        filters = statement_filters(statement)

        for auth_session in self.auth_sessions:
            if filters.get("refresh_token_hash") != auth_session.refresh_token_hash:
                continue

            if filters.get("refresh_token_jti") not in (None, auth_session.refresh_token_jti):
                continue

            if filters.get("user_id") not in (None, auth_session.user_id):
                continue

            if filters.get("organization_id") not in (None, auth_session.organization_id):
                continue

            if auth_session.revoked_at is not None:
                continue

            if auth_session.expires_at <= datetime.now(UTC):
                continue

            self.last_active_auth_session = auth_session
            return auth_session

        return None

    def add(self, instance: object) -> None:
        if isinstance(instance, AuthSession):
            if instance.id is None:
                instance.id = uuid4()
            self.auth_sessions.append(instance)

    def commit(self) -> None:
        return None

    def execute(self, statement: object) -> "FakeExecuteResult":
        if self.force_revoke_rowcount_zero:
            return FakeExecuteResult(rowcount=0)

        filters = statement_filters(statement)

        for auth_session in self.auth_sessions:
            if filters.get("id") != auth_session.id:
                continue

            if filters.get("refresh_token_hash") != auth_session.refresh_token_hash:
                continue

            if filters.get("refresh_token_jti") != auth_session.refresh_token_jti:
                continue

            if filters.get("user_id") != auth_session.user_id:
                continue

            if filters.get("organization_id") != auth_session.organization_id:
                continue

            if auth_session.revoked_at is not None:
                continue

            if auth_session.expires_at <= datetime.now(UTC):
                continue

            auth_session.revoked_at = datetime.now(UTC)
            return FakeExecuteResult(rowcount=1)

        return FakeExecuteResult(rowcount=0)


class FakeScalarResult:
    def __init__(self, users: list[UserRecord]) -> None:
        self.users = users

    def all(self) -> list[UserRecord]:
        return self.users


class FakeExecuteResult:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


def statement_entity(statement: object) -> type[object] | None:
    descriptions = getattr(statement, "column_descriptions", ())

    if not descriptions:
        return None

    entity = descriptions[0].get("entity")
    return entity if isinstance(entity, type) else None


def statement_filters(statement: object) -> dict[str, object]:
    filters: dict[str, object] = {}

    for criterion in getattr(statement, "_where_criteria", ()):
        left = getattr(criterion, "left", None)
        right = getattr(criterion, "right", None)
        column_name = getattr(left, "name", None)

        if column_name and hasattr(right, "value"):
            filters[column_name] = right.value

    return filters


@pytest.fixture
def profile() -> AuthenticatedUser:
    return AuthenticatedUser(
        id=uuid4(),
        organization_id=uuid4(),
        email="admin@example.local",
        full_name="Demo Admin",
        is_active=True,
        organization_name="Demo Organization",
        organization_slug="demo",
        roles=("admin",),
        permissions=("admin.manage", "crm.read"),
        modules=("crm",),
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        api_cors_origins=("http://localhost:3000",),
        jwt_secret="test-jwt-secret-with-enough-length",
    )


def make_client(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
    password: str = "correct-password",
) -> tuple[TestClient, FakeSession]:
    app = create_app(settings)
    user_record = UserRecord(id=profile.id, password_hash=hash_password(password))
    fake_session = FakeSession(user_record)

    app.dependency_overrides[get_db_session] = lambda: fake_session
    monkeypatch.setattr("app.auth.routes.get_user_profile_by_id", lambda session, user_id: profile)
    monkeypatch.setattr("app.auth.dependencies.get_user_profile_by_id", lambda session, user_id: profile)

    return TestClient(app), fake_session


def test_login_success_sets_http_only_auth_cookies(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
) -> None:
    client, fake_session = make_client(monkeypatch, settings, profile)

    response = client.post(
        "/auth/login",
        json={"email": "ADMIN@example.local", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "admin@example.local"
    assert "access" not in response.json()
    assert "refresh" not in response.json()
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert settings.auth_access_cookie_name in set_cookie
    assert settings.auth_refresh_cookie_name in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert len(fake_session.auth_sessions) == 1
    assert fake_session.auth_sessions[0].refresh_token_hash == hash_refresh_token(
        client.cookies.get(settings.auth_refresh_cookie_name) or ""
    )


def test_login_failure_rejects_bad_password(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
) -> None:
    client, _ = make_client(monkeypatch, settings, profile)

    response = client.post(
        "/auth/login",
        json={"email": "admin@example.local", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_requires_access_cookie(settings: Settings) -> None:
    client = TestClient(create_app(settings))

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
) -> None:
    client, _ = make_client(monkeypatch, settings, profile)
    client.post("/auth/login", json={"email": "admin@example.local", "password": "correct-password"})

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["roles"] == ["admin"]


def test_refresh_rotates_refresh_session_and_rejects_old_token(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
) -> None:
    client, fake_session = make_client(monkeypatch, settings, profile)
    client.post("/auth/login", json={"email": "admin@example.local", "password": "correct-password"})
    old_refresh_token = client.cookies.get(settings.auth_refresh_cookie_name)
    client.cookies.delete(settings.auth_access_cookie_name)

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert response.json()["refreshTokenPolicy"] == "server_session_rotation"
    assert settings.auth_access_cookie_name in response.headers.get("set-cookie", "")
    assert settings.auth_refresh_cookie_name in response.headers.get("set-cookie", "")
    assert client.cookies.get(settings.auth_refresh_cookie_name) != old_refresh_token
    assert len(fake_session.auth_sessions) == 2
    assert fake_session.auth_sessions[0].revoked_at is not None
    assert fake_session.auth_sessions[1].revoked_at is None

    client.cookies.set(settings.auth_refresh_cookie_name, old_refresh_token or "")

    reused_response = client.post("/auth/refresh")

    assert reused_response.status_code == 401
    assert len(fake_session.auth_sessions) == 2
    assert sum(auth_session.revoked_at is None for auth_session in fake_session.auth_sessions) == 1


def test_refresh_rejects_when_active_session_revoke_update_misses(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
) -> None:
    client, fake_session = make_client(monkeypatch, settings, profile)
    client.post("/auth/login", json={"email": "admin@example.local", "password": "correct-password"})
    old_refresh_token = client.cookies.get(settings.auth_refresh_cookie_name)
    client.cookies.delete(settings.auth_access_cookie_name)
    fake_session.force_revoke_rowcount_zero = True

    response = client.post("/auth/refresh")

    assert fake_session.last_active_auth_session is fake_session.auth_sessions[0]
    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert client.cookies.get(settings.auth_refresh_cookie_name) == old_refresh_token
    assert len(fake_session.auth_sessions) == 1
    assert fake_session.auth_sessions[0].revoked_at is None


def test_logout_clears_auth_cookies(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    profile: AuthenticatedUser,
) -> None:
    client, _ = make_client(monkeypatch, settings, profile)
    client.post("/auth/login", json={"email": "admin@example.local", "password": "correct-password"})
    refresh_token = client.cookies.get(settings.auth_refresh_cookie_name)

    response = client.post("/auth/logout")

    set_cookie = response.headers.get("set-cookie", "").lower()
    assert response.status_code == 200
    assert settings.auth_access_cookie_name in set_cookie
    assert settings.auth_refresh_cookie_name in set_cookie
    assert "max-age=0" in set_cookie

    client.cookies.set(settings.auth_refresh_cookie_name, refresh_token or "")

    refresh_response = client.post("/auth/refresh")

    assert refresh_response.status_code == 401


def test_rbac_helpers_allow_and_deny(profile: AuthenticatedUser) -> None:
    assert require_permission("crm.read")(profile) == profile
    assert require_role("admin")(profile) == profile
    assert require_module("crm")(profile) == profile

    with pytest.raises(HTTPException) as permission_error:
        require_permission("crm.write")(profile)

    with pytest.raises(HTTPException) as role_error:
        require_role("manager")(profile)

    with pytest.raises(HTTPException) as module_error:
        require_module("analytics")(profile)

    assert permission_error.value.status_code == 403
    assert role_error.value.status_code == 403
    assert module_error.value.status_code == 403
