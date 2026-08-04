from os import environ
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.communications.poll_cooldown import reset_poll_cooldowns
from app.config import Settings
from app.db.models import Communication, CommunicationThread, Contact, EventLog, ModuleToggle, Organization
from app.db.seed import seed_demo_data
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from tests.test_migrations import alembic_config, reset_public_schema

TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
requires_test_database = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for communications integration tests",
)


@pytest.fixture(autouse=True)
def reset_telegram_poll_cooldowns() -> None:
    reset_poll_cooldowns()
    yield
    reset_poll_cooldowns()


@pytest.fixture
def comm_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-with-enough-length-for-comms")
    monkeypatch.setenv("TELEGRAM_ENABLED", "false")
    return Settings.from_env()


@pytest.fixture
def seeded_comm_db(monkeypatch: pytest.MonkeyPatch, comm_settings: Settings) -> None:
    from alembic import command

    monkeypatch.setenv("SEED_DEMO", "true")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "comm-test-password")
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
        json={"email": "admin@example.local", "password": "comm-test-password"},
    )
    assert response.status_code == 200
    return client


@requires_test_database
def test_communications_timeline_and_message_with_event_linkage(
    seeded_comm_db: None,
    comm_settings: Settings,
) -> None:
    client = login_client(comm_settings)

    contact = client.get("/crm/contacts").json()[0]
    contact_id = contact["id"]

    create_response = client.post(
        "/communications/messages",
        json={
            "channel_type": "email",
            "direction": "inbound",
            "body": "Hello from MVP communications",
            "contact_id": contact_id,
        },
    )
    assert create_response.status_code == 201
    message = create_response.json()
    assert message["contact_id"] == contact_id
    assert message["body"] == "Hello from MVP communications"

    timeline = client.get(f"/communications/timeline?contact_id={contact_id}")
    assert timeline.status_code == 200
    items = timeline.json()
    assert any(item["id"] == message["id"] for item in items)

    events = client.get(f"/crm/event-logs?entity_type=contact&entity_id={contact_id}")
    assert events.status_code == 200
    event_types = {item["event_type"] for item in events.json()}
    assert "communication.received" in event_types


@requires_test_database
def test_communications_integrations_status_stub_vs_live(
    seeded_comm_db: None,
    comm_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = login_client(comm_settings)

    status_response = client.get("/communications/integrations/status")
    assert status_response.status_code == 200
    integrations = {item["channel"]: item for item in status_response.json()["integrations"]}

    assert integrations["telegram"]["mode"] == "stub"
    assert integrations["gmail"]["mode"] == "stub"
    assert integrations["calendar"]["mode"] == "stub"

    poll_response = client.post("/communications/telegram/poll")
    assert poll_response.status_code == 503

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ENABLED", "false")
    disabled_settings = Settings.from_env()
    disabled_client = TestClient(create_app(disabled_settings))
    login = disabled_client.post(
        "/auth/login",
        json={"email": "admin@example.local", "password": "comm-test-password"},
    )
    assert login.status_code == 200

    disabled_status = disabled_client.get("/communications/integrations/status").json()
    telegram = next(item for item in disabled_status["integrations"] if item["channel"] == "telegram")
    assert telegram["mode"] == "disabled"


@requires_test_database
def test_communications_telegram_poll_happy_path(
    seeded_comm_db: None,
    comm_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    live_settings = Settings.from_env()

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None
        contact = session.scalar(
            select(Contact).where(
                Contact.organization_id == org.id,
                Contact.full_name == "Baseline Contact",
            )
        )
        assert contact is not None
        contact.meta = {**contact.meta, "telegram_chat_id": "12345"}
        session.commit()
        contact_id = contact.id

    engine.dispose()

    client = TestClient(create_app(live_settings))
    login = client.post(
        "/auth/login",
        json={"email": "admin@example.local", "password": "comm-test-password"},
    )
    assert login.status_code == 200

    fake_updates = [
        {
            "update_id": 1,
            "message": {
                "message_id": 99,
                "chat": {"id": 12345},
                "text": "Telegram inbound test",
                "from": {"username": "tester"},
            },
        }
    ]

    with patch("app.communications.service.fetch_telegram_updates", return_value=fake_updates):
        poll_response = client.post("/communications/telegram/poll")

    assert poll_response.status_code == 200
    assert poll_response.json() == {
        "processed": 1,
        "created": 1,
        "skipped_unmatched": 0,
        "mode": "live",
    }

    timeline = client.get(f"/communications/timeline?contact_id={contact_id}")
    assert timeline.status_code == 200
    assert any(item["channel_type"] == "telegram" for item in timeline.json())

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        comm = session.scalar(
            select(Communication).where(Communication.external_message_id == "99")
        )
        assert comm is not None
        event = session.scalar(
            select(EventLog).where(
                EventLog.entity_type == "communication",
                EventLog.entity_id == comm.id,
                EventLog.event_type == "communication.received",
            )
        )
        assert event is not None

    engine.dispose()


@requires_test_database
def test_communications_module_and_tenant_guards(
    seeded_comm_db: None,
    comm_settings: Settings,
) -> None:
    client = login_client(comm_settings)
    contact_id = client.get("/crm/contacts").json()[0]["id"]

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        other_org = Organization(name="Other Org Comms", slug="other-comms")
        session.add(other_org)
        session.flush()

        other_contact = Contact(
            organization_id=other_org.id,
            full_name="Secret Contact",
        )
        session.add(other_contact)
        session.flush()
        other_contact_id = other_contact.id

        toggle = session.scalar(
            select(ModuleToggle).where(
                ModuleToggle.organization_id == org.id,
                ModuleToggle.module_key == "communications",
            )
        )
        assert toggle is not None
        toggle.enabled = False
        session.commit()

    assert client.get(f"/communications/timeline?contact_id={contact_id}").status_code == 403
    assert client.get(f"/communications/timeline?contact_id={other_contact_id}").status_code == 403

    engine.dispose()


@requires_test_database
def test_communications_rejects_stub_channel_create(
    seeded_comm_db: None,
    comm_settings: Settings,
) -> None:
    client = login_client(comm_settings)
    contact_id = client.get("/crm/contacts").json()[0]["id"]

    gmail_response = client.post(
        "/communications/messages",
        json={
            "channel_type": "gmail",
            "body": "blocked",
            "contact_id": contact_id,
        },
    )
    assert gmail_response.status_code == 400

    calendar_response = client.post(
        json={
            "channel_type": "calendar",
            "body": "blocked",
            "contact_id": contact_id,
        },
    )
    assert calendar_response.status_code == 400


@requires_test_database
def test_communications_rejects_manual_telegram_create(
    seeded_comm_db: None,
    comm_settings: Settings,
) -> None:
    client = login_client(comm_settings)
    contact_id = client.get("/crm/contacts").json()[0]["id"]

    telegram_response = client.post(
        "/communications/messages",
        json={
            "channel_type": "telegram",
            "direction": "inbound",
            "body": "spoofed inbound",
            "contact_id": contact_id,
        },
    )
    assert telegram_response.status_code == 400
    assert "telegram/poll" in telegram_response.json()["detail"]


@requires_test_database
def test_communications_telegram_poll_cooldown(
    seeded_comm_db: None,
    comm_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_POLL_COOLDOWN_SECONDS", "30")
    live_settings = Settings.from_env()
    client = TestClient(create_app(live_settings))
    login = client.post(
        "/auth/login",
        json={"email": "admin@example.local", "password": "comm-test-password"},
    )
    assert login.status_code == 200

    with patch("app.communications.service.fetch_telegram_updates", return_value=[]):
        first = client.post("/communications/telegram/poll")
        second = client.post("/communications/telegram/poll")

    assert first.status_code == 200
    assert second.status_code == 429
    assert "cooldown" in second.json()["detail"].lower()


@requires_test_database
def test_communications_telegram_poll_skips_unmatched_safely(
    seeded_comm_db: None,
    comm_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    live_settings = Settings.from_env()
    client = TestClient(create_app(live_settings))
    login = client.post(
        "/auth/login",
        json={"email": "admin@example.local", "password": "comm-test-password"},
    )
    assert login.status_code == 200

    fake_updates = [
        {
            "update_id": 2,
            "message": {
                "message_id": 1001,
                "chat": {"id": 99999},
                "text": "Unmatched chat",
                "from": {"username": "stranger"},
            },
        }
    ]

    with patch("app.communications.service.fetch_telegram_updates", return_value=fake_updates):
        poll_response = client.post("/communications/telegram/poll")

    assert poll_response.status_code == 200
    assert poll_response.json() == {
        "processed": 1,
        "created": 0,
        "skipped_unmatched": 1,
        "mode": "live",
    }

    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        org = session.scalar(select(Organization).where(Organization.slug == "demo"))
        assert org is not None

        orphan_threads = session.scalar(
            select(func.count())
            .select_from(CommunicationThread)
            .where(
                CommunicationThread.organization_id == org.id,
                CommunicationThread.channel_type == "telegram",
                CommunicationThread.external_thread_id == "99999",
            )
        )
        assert orphan_threads == 0

        orphan_messages = session.scalar(
            select(func.count())
            .select_from(Communication)
            .where(Communication.external_message_id == "1001")
        )
        assert orphan_messages == 0

    engine.dispose()
