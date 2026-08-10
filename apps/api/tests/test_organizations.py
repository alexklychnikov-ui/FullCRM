from datetime import UTC, datetime, timedelta
from os import environ

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.auth.passwords import hash_password
from app.config import Settings
from app.db.models import (
    Deal,
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.db.seed import seed_demo_data
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from tests.test_migrations import alembic_config, reset_public_schema

TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
requires_test_database = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for organizations integration tests",
)


@pytest.fixture
def org_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-with-enough-length-for-org-settings")
    return Settings.from_env()


@pytest.fixture
def seeded_org_db(monkeypatch: pytest.MonkeyPatch, org_settings: Settings) -> None:
    from alembic import command

    monkeypatch.setenv("SEED_DEMO", "true")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "org-settings-test-password")
    config = alembic_config()
    reset_public_schema(TEST_DATABASE_URL)
    command.upgrade(config, "head")

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        seed_demo_data(session)

    engine.dispose()


def login_client(settings: Settings, email: str = "admin@example.local", password: str = "org-settings-test-password") -> TestClient:
    client = TestClient(create_app(settings))
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return client


@requires_test_database
def test_get_settings_returns_defaults_when_empty(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    client = login_client(org_settings)
    response = client.get("/organizations/me/settings")
    assert response.status_code == 200
    assert response.json() == {
        "analytics": {
            "stale_deal_days": 7,
            "activity_window_days": 7,
        }
    }


@requires_test_database
def test_patch_settings_deep_merge_persists(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None
        org.settings = {"other": {"keep": True}, "analytics": {"activity_window_days": 14}}
        flag_modified(org, "settings")
        session.commit()

    client = login_client(org_settings)
    patch = client.patch(
        "/organizations/me/settings",
        json={"analytics": {"stale_deal_days": 3}},
    )
    assert patch.status_code == 200
    assert patch.json()["analytics"]["stale_deal_days"] == 3
    assert patch.json()["analytics"]["activity_window_days"] == 14

    got = client.get("/organizations/me/settings")
    assert got.status_code == 200
    assert got.json()["analytics"]["stale_deal_days"] == 3
    assert got.json()["analytics"]["activity_window_days"] == 14

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None
        assert org.settings["other"] == {"keep": True}
        assert org.settings["analytics"]["stale_deal_days"] == 3
        assert org.settings["analytics"]["activity_window_days"] == 14

    engine.dispose()


@requires_test_database
def test_settings_requires_auth_and_admin_manage(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    anonymous = TestClient(create_app(org_settings))
    assert anonymous.get("/organizations/me/settings").status_code == 401
    assert anonymous.patch(
        "/organizations/me/settings",
        json={"analytics": {"stale_deal_days": 3}},
    ).status_code == 401

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        read_role = Role(organization_id=org.id, name="reader", description="read only")
        session.add(read_role)
        session.flush()

        crm_read = session.scalar(select(Permission).where(Permission.key == "crm.read"))
        assert crm_read is not None
        session.add(
            RolePermission(
                organization_id=org.id,
                role_id=read_role.id,
                permission_id=crm_read.id,
            )
        )

        reader = User(
            organization_id=org.id,
            email="reader@example.local",
            full_name="Reader User",
            password_hash=hash_password("reader-password"),
        )
        session.add(reader)
        session.flush()
        session.add(
            UserRole(
                organization_id=org.id,
                user_id=reader.id,
                role_id=read_role.id,
            )
        )
        session.commit()

    reader_client = login_client(org_settings, email="reader@example.local", password="reader-password")
    assert reader_client.get("/organizations/me/settings").status_code == 403
    assert reader_client.patch(
        "/organizations/me/settings",
        json={"analytics": {"stale_deal_days": 3}},
    ).status_code == 403

    engine.dispose()


@requires_test_database
def test_modules_get_and_patch(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    client = login_client(org_settings)

    listing = client.get("/organizations/me/modules")
    assert listing.status_code == 200
    payload = listing.json()
    keys = {item["module_key"] for item in payload["modules"]}
    assert keys == {"crm", "communications", "ai", "analytics"}
    assert all(item["enabled"] for item in payload["modules"])

    patched = client.patch(
        "/organizations/me/modules",
        json={
            "modules": [
                {"module_key": "communications", "enabled": False},
                {"module_key": "ai", "enabled": False},
            ]
        },
    )
    assert patched.status_code == 200
    by_key = {item["module_key"]: item["enabled"] for item in patched.json()["modules"]}
    assert by_key["crm"] is True
    assert by_key["communications"] is False
    assert by_key["ai"] is False
    assert by_key["analytics"] is True

    assert client.patch(
        "/organizations/me/modules",
        json={"modules": [{"module_key": "crm", "enabled": False}]},
    ).status_code == 400


@requires_test_database
def test_modules_requires_auth_and_admin_manage(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    anonymous = TestClient(create_app(org_settings))
    assert anonymous.get("/organizations/me/modules").status_code == 401
    assert anonymous.patch(
        "/organizations/me/modules",
        json={"modules": [{"module_key": "ai", "enabled": False}]},
    ).status_code == 401

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        read_role = Role(organization_id=org.id, name="reader-modules", description="read only")
        session.add(read_role)
        session.flush()

        crm_read = session.scalar(select(Permission).where(Permission.key == "crm.read"))
        assert crm_read is not None
        session.add(
            RolePermission(
                organization_id=org.id,
                role_id=read_role.id,
                permission_id=crm_read.id,
            )
        )

        reader = User(
            organization_id=org.id,
            email="reader-modules@example.local",
            full_name="Reader Modules",
            password_hash=hash_password("reader-password"),
        )
        session.add(reader)
        session.flush()
        session.add(
            UserRole(
                organization_id=org.id,
                user_id=reader.id,
                role_id=read_role.id,
            )
        )
        session.commit()

    reader_client = login_client(org_settings, email="reader-modules@example.local", password="reader-password")
    assert reader_client.get("/organizations/me/modules").status_code == 403
    assert reader_client.patch(
        "/organizations/me/modules",
        json={"modules": [{"module_key": "ai", "enabled": False}]},
    ).status_code == 403

    engine.dispose()


@requires_test_database
def test_analytics_uses_org_stale_threshold(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None
        org.settings = {"analytics": {"stale_deal_days": 3, "activity_window_days": 7}}
        flag_modified(org, "settings")

        deal = session.scalar(select(Deal).where(Deal.organization_id == org.id, Deal.title == "Baseline Deal"))
        assert deal is not None
        deal.status = "open"
        deal.updated_at = datetime.now(UTC) - timedelta(days=5)
        session.commit()

    client = login_client(org_settings)
    summary = client.get("/analytics/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["follow_up"]["stale_threshold_days"] == 3
    assert payload["follow_up"]["overdue_count"] >= 1
    assert any(item["title"] == "Baseline Deal" for item in payload["follow_up"]["deals"])

    engine.dispose()


@requires_test_database
def test_admin_lists_default_roles(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    client = login_client(org_settings)
    response = client.get("/organizations/me/roles")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["roles"]}
    assert names == {"admin", "manager", "analyst"}


@requires_test_database
def test_admin_creates_manager_user_and_manager_forbidden_on_settings(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    client = login_client(org_settings)
    created = client.post(
        "/organizations/me/users",
        json={
            "email": "manager@example.local",
            "full_name": "Sales Manager",
            "password": "manager-password",
            "roles": ["manager"],
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["email"] == "manager@example.local"
    assert body["roles"] == ["manager"]
    assert body["is_active"] is True

    manager_client = login_client(
        org_settings,
        email="manager@example.local",
        password="manager-password",
    )
    assert manager_client.get("/organizations/me/settings").status_code == 403


@requires_test_database
def test_admin_deactivates_user_and_login_fails(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    client = login_client(org_settings)
    created = client.post(
        "/organizations/me/users",
        json={
            "email": "temp@example.local",
            "full_name": "Temp User",
            "password": "temp-password",
            "roles": ["analyst"],
        },
    )
    assert created.status_code == 200
    user_id = created.json()["id"]

    patched = client.patch(
        f"/organizations/me/users/{user_id}",
        json={"is_active": False},
    )
    assert patched.status_code == 200
    assert patched.json()["is_active"] is False

    anon = TestClient(create_app(org_settings))
    login = anon.post(
        "/auth/login",
        json={"email": "temp@example.local", "password": "temp-password"},
    )
    assert login.status_code == 401


@requires_test_database
def test_admin_cannot_deactivate_self(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    client = login_client(org_settings)
    me = client.get("/auth/me")
    assert me.status_code == 200
    admin_id = me.json()["user"]["id"]

    response = client.patch(
        f"/organizations/me/users/{admin_id}",
        json={"is_active": False},
    )
    assert response.status_code == 400


@requires_test_database
def test_users_list_requires_admin_manage(
    seeded_org_db: None,
    org_settings: Settings,
) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        read_role = Role(organization_id=org.id, name="reader-users", description="read only")
        session.add(read_role)
        session.flush()

        crm_read = session.scalar(select(Permission).where(Permission.key == "crm.read"))
        assert crm_read is not None
        session.add(
            RolePermission(
                organization_id=org.id,
                role_id=read_role.id,
                permission_id=crm_read.id,
            )
        )

        reader = User(
            organization_id=org.id,
            email="reader-users@example.local",
            full_name="Reader Users",
            password_hash=hash_password("reader-password"),
        )
        session.add(reader)
        session.flush()
        session.add(
            UserRole(
                organization_id=org.id,
                user_id=reader.id,
                role_id=read_role.id,
            )
        )
        session.commit()

    reader_client = login_client(
        org_settings,
        email="reader-users@example.local",
        password="reader-password",
    )
    assert reader_client.get("/organizations/me/users").status_code == 403

    engine.dispose()
