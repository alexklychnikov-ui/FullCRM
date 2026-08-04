from os import environ

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.passwords import hash_password
from app.config import Settings
from app.db.models import (
    Company,
    Deal,
    EventLog,
    ModuleToggle,
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
    reason="TEST_DATABASE_URL is required for CRM integration tests",
)


@pytest.fixture
def crm_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-with-enough-length-for-crm")
    return Settings.from_env()


@pytest.fixture
def seeded_crm_db(monkeypatch: pytest.MonkeyPatch, crm_settings: Settings) -> None:
    from alembic import command

    monkeypatch.setenv("SEED_DEMO", "true")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "crm-test-password")
    config = alembic_config()
    reset_public_schema(TEST_DATABASE_URL)
    command.upgrade(config, "head")

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        seed_demo_data(session)

    engine.dispose()


def login_client(settings: Settings) -> TestClient:
    client = TestClient(create_app(settings))
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.local", "password": "crm-test-password"},
    )
    assert response.status_code == 200
    return client


@requires_test_database
def test_crm_company_contact_deal_crud_and_events(
    seeded_crm_db: None,
    crm_settings: Settings,
) -> None:
    client = login_client(crm_settings)

    company_response = client.post(
        "/crm/companies",
        json={"name": "Acme Corp", "domain": "acme.local"},
    )
    assert company_response.status_code == 201
    company_id = company_response.json()["id"]

    contact_response = client.post(
        "/crm/contacts",
        json={
            "full_name": "Jane Doe",
            "email": "jane@acme.local",
            "company_id": company_id,
        },
    )
    assert contact_response.status_code == 201
    contact_id = contact_response.json()["id"]

    pipelines = client.get("/crm/pipelines")
    assert pipelines.status_code == 200
    pipeline = pipelines.json()[0]
    stage_id = pipeline["stages"][0]["id"]

    deal_response = client.post(
        "/crm/deals",
        json={
            "title": "Enterprise license",
            "pipeline_id": pipeline["id"],
            "stage_id": stage_id,
            "company_id": company_id,
            "contact_id": contact_id,
            "amount": "50000.00",
        },
    )
    assert deal_response.status_code == 201
    deal = deal_response.json()
    deal_id = deal["id"]
    assert deal["owner_user_id"] is not None

    patch_response = client.patch(
        f"/crm/deals/{deal_id}",
        json={"status": "negotiation"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "negotiation"

    next_stage_id = pipeline["stages"][1]["id"]
    transition_response = client.post(
        f"/crm/deals/{deal_id}/transition",
        json={"stage_id": next_stage_id},
    )
    assert transition_response.status_code == 200
    assert transition_response.json()["stage_id"] == next_stage_id

    events = client.get(f"/crm/event-logs?entity_type=deal&entity_id={deal_id}")
    assert events.status_code == 200
    event_types = {item["event_type"] for item in events.json()}
    assert "deal.created" in event_types
    assert "deal.updated" in event_types
    assert "deal.stage_changed" in event_types


@requires_test_database
def test_crm_requires_auth_and_permissions(
    seeded_crm_db: None,
    crm_settings: Settings,
) -> None:
    anonymous = TestClient(create_app(crm_settings))
    assert anonymous.get("/crm/companies").status_code == 401

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

    reader_client = TestClient(create_app(crm_settings))
    login = reader_client.post(
        "/auth/login",
        json={"email": "reader@example.local", "password": "reader-password"},
    )
    assert login.status_code == 200

    assert reader_client.get("/crm/companies").status_code == 200
    assert reader_client.post("/crm/companies", json={"name": "Blocked Co"}).status_code == 403

    engine.dispose()


@requires_test_database
def test_crm_tenant_isolation(
    seeded_crm_db: None,
    crm_settings: Settings,
) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        other_org = Organization(name="Other Org", slug="other")
        session.add(other_org)
        session.flush()

        other_company = Company(organization_id=other_org.id, name="Secret Co")
        session.add(other_company)
        session.flush()
        other_company_id = other_company.id
        session.commit()

    client = login_client(crm_settings)
    response = client.get(f"/crm/companies/{other_company_id}")

    assert response.status_code == 404

    engine.dispose()


@requires_test_database
def test_crm_module_guard(
    seeded_crm_db: None,
    crm_settings: Settings,
) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        toggle = session.scalar(
            select(ModuleToggle).where(
                ModuleToggle.organization_id == org.id,
                ModuleToggle.module_key == "crm",
            )
        )
        assert toggle is not None
        toggle.enabled = False
        session.commit()

    client = login_client(crm_settings)
    assert client.get("/crm/companies").status_code == 403

    engine.dispose()


@requires_test_database
def test_crm_list_endpoints_return_seeded_baseline(
    seeded_crm_db: None,
    crm_settings: Settings,
) -> None:
    client = login_client(crm_settings)

    companies = client.get("/crm/companies").json()
    contacts = client.get("/crm/contacts").json()
    deals = client.get("/crm/deals").json()

    assert any(item["name"] == "Baseline Company" for item in companies)
    assert any(item["full_name"] == "Baseline Contact" for item in contacts)
    assert any(item["title"] == "Baseline Deal" for item in deals)

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        deal_count = session.scalar(select(Deal).where(Deal.title == "Baseline Deal"))
        assert deal_count is not None
        event_count = session.scalar(
            select(EventLog).where(
                EventLog.deal_id == deal_count.id,
                EventLog.event_type == "seed.baseline",
            )
        )
        assert event_count is not None

    engine.dispose()
