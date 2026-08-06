from datetime import UTC, datetime, timedelta
from os import environ

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db.models import Deal, ModuleToggle, Organization, PipelineStage
from app.db.seed import seed_demo_data
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from tests.test_migrations import alembic_config, reset_public_schema

TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
requires_test_database = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for analytics integration tests",
)


@pytest.fixture
def analytics_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-with-enough-length-for-analytics")
    return Settings.from_env()


@pytest.fixture
def seeded_analytics_db(monkeypatch: pytest.MonkeyPatch, analytics_settings: Settings) -> None:
    from alembic import command

    monkeypatch.setenv("SEED_DEMO", "true")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "analytics-test-password")
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
        json={"email": "admin@example.local", "password": "analytics-test-password"},
    )
    assert response.status_code == 200
    return client


@requires_test_database
def test_analytics_summary_matches_seed_and_pipeline(
    seeded_analytics_db: None,
    analytics_settings: Settings,
) -> None:
    client = login_client(analytics_settings)
    response = client.get("/analytics/summary")
    assert response.status_code == 200

    payload = response.json()
    assert payload["refresh_strategy"] == "query_time"
    assert payload["conversion"]["total_deals"] >= 1
    assert payload["activity"]["total_events"] >= 1

    stage_names = {item["stage_name"] for item in payload["deals_by_stage"]}
    assert "New" in stage_names
    assert sum(item["count"] for item in payload["deals_by_stage"]) == payload["conversion"]["total_deals"]

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        won_stage = session.scalar(
            select(PipelineStage).where(
                PipelineStage.organization_id == org.id,
                PipelineStage.name == "Won",
            )
        )
        assert won_stage is not None

        deal = session.scalar(select(Deal).where(Deal.organization_id == org.id, Deal.title == "Baseline Deal"))
        assert deal is not None
        deal.stage_id = won_stage.id
        deal.updated_at = datetime.now(UTC) - timedelta(days=10)
        session.commit()

    updated = client.get("/analytics/summary").json()
    assert updated["conversion"]["won_deals"] >= 1
    assert updated["conversion"]["win_rate"] is not None
    assert updated["follow_up"]["overdue_count"] >= 0
    assert updated["follow_up"]["stale_threshold_days"] == 7

    engine.dispose()


@requires_test_database
def test_analytics_follow_up_respects_org_settings_threshold(
    seeded_analytics_db: None,
    analytics_settings: Settings,
) -> None:
    from sqlalchemy.orm.attributes import flag_modified

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None
        org.settings = {"analytics": {"stale_deal_days": 3}}
        flag_modified(org, "settings")

        deal = session.scalar(select(Deal).where(Deal.organization_id == org.id, Deal.title == "Baseline Deal"))
        assert deal is not None
        deal.status = "open"
        deal.updated_at = datetime.now(UTC) - timedelta(days=5)
        session.commit()

    client = login_client(analytics_settings)
    payload = client.get("/analytics/summary").json()
    assert payload["follow_up"]["stale_threshold_days"] == 3
    assert payload["follow_up"]["overdue_count"] >= 1

    engine.dispose()


@requires_test_database
def test_analytics_requires_auth_and_module(
    seeded_analytics_db: None,
    analytics_settings: Settings,
) -> None:
    anonymous = TestClient(create_app(analytics_settings))
    assert anonymous.get("/analytics/summary").status_code == 401

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        toggle = session.scalar(
            select(ModuleToggle).where(
                ModuleToggle.organization_id == org.id,
                ModuleToggle.module_key == "analytics",
            )
        )
        assert toggle is not None
        toggle.enabled = False
        session.commit()

    client = login_client(analytics_settings)
    assert client.get("/analytics/summary").status_code == 403

    engine.dispose()
