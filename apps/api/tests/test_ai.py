from os import environ

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db.models import ModuleToggle, Organization, Permission, Role, RolePermission, User, UserRole
from app.db.seed import seed_demo_data
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from tests.test_migrations import alembic_config, reset_public_schema

TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
requires_test_database = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for AI integration tests",
)


@pytest.fixture
def ai_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-with-enough-length-for-ai")
    monkeypatch.setenv("AI_MOCK", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return Settings.from_env()


@pytest.fixture
def seeded_ai_db(monkeypatch: pytest.MonkeyPatch, ai_settings: Settings) -> None:
    from alembic import command

    monkeypatch.setenv("SEED_DEMO", "true")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "ai-test-password")
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
        json={"email": "admin@example.local", "password": "ai-test-password"},
    )
    assert response.status_code == 200
    return client


def test_settings_ai_mock_defaults_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("AI_MOCK", raising=False)

    settings = Settings.from_env()
    assert settings.ai_mock is True


def test_settings_openai_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("AI_MOCK", "false")

    settings = Settings.from_env()
    assert settings.openai_api_key == "sk-test-key"
    assert settings.ai_mock is False
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-with-enough-length-for-ai")
    monkeypatch.setenv("AI_MOCK", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings.from_env()
    assert settings.ai_mock is True
    assert settings.openai_api_key is None


def test_settings_ai_model_defaults_to_gpt_4o_mini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("AI_MODEL", raising=False)

    settings = Settings.from_env()
    assert settings.ai_model == "gpt-4o-mini"


def test_settings_ai_model_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AI_MODEL", "gpt-4.1-mini")

    settings = Settings.from_env()
    assert settings.ai_model == "gpt-4.1-mini"


def test_settings_ai_model_prefers_ai_model_over_openai_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")

    settings = Settings.from_env()
    assert settings.ai_model == "gpt-4o-mini"


def test_settings_ai_model_openai_model_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")

    settings = Settings.from_env()
    assert settings.ai_model == "gpt-5.4-mini-2026-03-17"


def test_mock_insights_use_russian_text() -> None:
    from uuid import uuid4

    from app.ai.context import DealAiContext
    from app.ai.providers.mock import generate_mock_insights

    context = DealAiContext(
        deal_id=uuid4(),
        title="Baseline Deal",
        amount="5000",
        currency="USD",
        status="open",
        stage_name="Qualified",
        company_name="Demo Co",
        has_contact=True,
        days_open=5,
        recent_event_count=2,
        communications=(),
        deal_events=(),
        related_deals=(),
    )
    payload = generate_mock_insights(context)

    assert "Ранний" not in payload.score.label
    assert "Квалифицирован" in payload.score.label or "затягивания" in payload.score.label.lower()
    assert any("\u0400" <= char <= "\u04ff" for char in payload.next_action.action)
    assert any("\u0400" <= char <= "\u04ff" for char in payload.draft_suggestion.body)


def test_mock_org_insights_use_russian_and_recommendations() -> None:
    from uuid import uuid4

    from app.ai.org_context import OrgAnalyticsAiContext, OrgTopDeal
    from app.ai.providers.mock import generate_mock_org_insights

    context = OrgAnalyticsAiContext(
        organization_id=uuid4(),
        summary={
            "conversion": {
                "open_deals": 12,
                "won_deals": 6,
                "win_rate": 33.3,
                "open_pipeline_amount": 30205000,
                "currency": "RUB",
            },
            "cycle": {"avg_days_to_close": 26.8, "won_sample_size": 6},
            "follow_up": {"overdue_count": 4},
            "activity": {"events_last_7_days": 20},
        },
        top_open_deals=(
            OrgTopDeal(
                title="Крупная сделка",
                stage_name="Qualified",
                status="open",
                amount=1000000,
                currency="RUB",
                days_since_update=5,
            ),
        ),
        stale_deals=(),
    )
    payload = generate_mock_org_insights(context)

    assert 0 <= payload.health.probability <= 100
    assert any("\u0400" <= char <= "\u04ff" for char in payload.health.label)
    assert any("\u0400" <= char <= "\u04ff" for char in payload.outlook)
    assert len(payload.recommendations) >= 2
    assert any("\u0400" <= char <= "\u04ff" for char in payload.planning)


def test_context_prompt_includes_communications_and_history() -> None:
    from uuid import uuid4

    from app.ai.context import (
        CommunicationSnippet,
        DealAiContext,
        RelatedDealSummary,
        context_to_prompt_payload,
    )

    context = DealAiContext(
        deal_id=uuid4(),
        title="Текущая",
        amount="12000",
        currency="RUB",
        status="open",
        stage_name="Qualified",
        company_name="МастерБыт",
        has_contact=True,
        days_open=12,
        recent_event_count=3,
        communications=(
            CommunicationSnippet(
                channel="email",
                direction="inbound",
                occurred_at="2026-08-01T10:00:00+00:00",
                body_preview="Клиент просит уточнить сроки",
            ),
        ),
        deal_events=(),
        related_deals=(
            RelatedDealSummary(
                title="Прошлая",
                status="open",
                stage_name="Won",
                amount="8000",
                currency="RUB",
                days_open=9,
                days_to_close=9,
                is_won=True,
                updated_at="2026-07-01T10:00:00+00:00",
            ),
        ),
    )
    payload = context_to_prompt_payload(context)

    assert payload["current_deal"]["days_open"] == 12
    assert payload["communications"][0]["body_preview"] == "Клиент просит уточнить сроки"
    assert payload["company_deal_history"]["won_count"] == 1
    assert payload["company_deal_history"]["avg_days_to_close_won"] == 9.0
    assert "качество и полнота коммуникации" in payload["analysis_focus"][0]


def test_sanitize_text_redacts_email_and_phone() -> None:
    from app.ai.context import _sanitize_text

    cleaned = _sanitize_text("Пишите на boss@example.com или +7 999 111-22-33 срочно")
    assert "@" not in cleaned
    assert "boss" not in cleaned
    assert "[email]" in cleaned
    assert "[phone]" in cleaned


@requires_test_database
def test_ai_status_endpoint(seeded_ai_db: None, ai_settings: Settings) -> None:
    client = login_client(ai_settings)
    response = client.get("/ai/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "mock"
    assert "score" in payload["use_cases"]


@requires_test_database
def test_ai_deal_insights_mock_mode(seeded_ai_db: None, ai_settings: Settings) -> None:
    client = login_client(ai_settings)
    deal_id = client.get("/crm/deals").json()[0]["id"]

    response = client.get(f"/ai/deals/{deal_id}/insights")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_mode"] == "mock"
    assert payload["advisory"] is True
    assert 0 <= payload["score"]["probability"] <= 100
    assert payload["next_action"]["action"]
    assert payload["draft_suggestion"]["body"]


@requires_test_database
def test_ai_requires_module_and_permission(
    seeded_ai_db: None,
    ai_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anonymous = TestClient(create_app(ai_settings))
    assert anonymous.get("/ai/status").status_code == 401

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        ai_toggle = session.scalar(
            select(ModuleToggle).where(
                ModuleToggle.organization_id == org.id,
                ModuleToggle.module_key == "ai",
            )
        )
        assert ai_toggle is not None
        ai_toggle.enabled = False
        session.commit()

    client = login_client(ai_settings)
    assert client.get("/ai/status").status_code == 403

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None
        ai_toggle = session.scalar(
            select(ModuleToggle).where(
                ModuleToggle.organization_id == org.id,
                ModuleToggle.module_key == "ai",
            )
        )
        assert ai_toggle is not None
        ai_toggle.enabled = True

        reader_role = Role(organization_id=org.id, name="ai-reader", description="ai read only")
        session.add(reader_role)
        session.flush()

        ai_read = session.scalar(select(Permission).where(Permission.key == "ai.read"))
        assert ai_read is not None
        session.add(
            RolePermission(
                organization_id=org.id,
                role_id=reader_role.id,
                permission_id=ai_read.id,
            )
        )

        reader = User(
            organization_id=org.id,
            email="ai-reader@example.local",
            full_name="AI Reader",
            password_hash="disabled",
        )
        session.add(reader)
        session.flush()
        session.add(
            UserRole(
                organization_id=org.id,
                user_id=reader.id,
                role_id=reader_role.id,
            )
        )
        session.commit()

    from app.auth.passwords import hash_password

    with session_factory() as session:
        reader = session.scalar(select(User).where(User.email == "ai-reader@example.local"))
        assert reader is not None
        reader.password_hash = hash_password("reader-password")
        session.commit()

    reader_client = TestClient(create_app(ai_settings))
    login = reader_client.post(
        "/auth/login",
        json={"email": "ai-reader@example.local", "password": "reader-password"},
    )
    assert login.status_code == 200
    assert reader_client.get("/ai/status").status_code == 200

    engine.dispose()


@requires_test_database
def test_ai_logs_exclude_pii(
    seeded_ai_db: None,
    ai_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    caplog.set_level(logging.INFO, logger="fullcrm.ai")
    client = login_client(ai_settings)
    deal = client.get("/crm/deals").json()[0]
    deal_id = deal["id"]

    response = client.get(f"/ai/deals/{deal_id}/insights")
    assert response.status_code == 200

    log_text = caplog.text.lower()
    assert "ai.call" in log_text or "org_id=" in log_text
    assert "@" not in log_text
    assert "sk-" not in log_text


@requires_test_database
def test_ai_degraded_on_openai_failure(
    seeded_ai_db: None,
    ai_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_MOCK", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-used")

    settings = Settings.from_env()
    client = login_client(settings)
    deal_id = client.get("/crm/deals").json()[0]["id"]

    from app.ai.providers import openai as openai_provider

    def fail_openai(*_args: object, **_kwargs: object) -> None:
        raise openai_provider.OpenAiProviderError("simulated outage")

    monkeypatch.setattr(openai_provider, "generate_openai_insights", fail_openai)

    response = client.get(f"/ai/deals/{deal_id}/insights")
    assert response.status_code == 200
    assert response.json()["provider_mode"] == "degraded"
