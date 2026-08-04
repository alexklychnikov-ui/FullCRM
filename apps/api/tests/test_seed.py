from os import environ

import pytest
from sqlalchemy import func, select

from app.db.models import (
    Communication,
    CommunicationThread,
    Contact,
    Deal,
    EventLog,
    ModuleToggle,
    Organization,
    Permission,
    Pipeline,
    PipelineStage,
    Role,
    User,
)
from app.db.seed import (
    SeedBlockedError,
    assert_demo_seed_allowed,
    demo_seed_allowed,
    main as seed_main,
    seed_demo_data,
)
from app.db.session import create_db_engine, create_session_factory
from tests.test_migrations import alembic_config, reset_public_schema


TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
requires_test_database = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for database seed integration tests",
)


@pytest.fixture
def allow_demo_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("SEED_DEMO", "true")


@pytest.fixture
def migrated_database(monkeypatch: pytest.MonkeyPatch, allow_demo_seed: None) -> None:
    from alembic import command

    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    config = alembic_config()
    reset_public_schema(TEST_DATABASE_URL)
    command.upgrade(config, "head")


def table_count(session_factory, model: type[object]) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(model)) or 0


def demo_counts(session_factory) -> tuple[int, ...]:
    return tuple(
        table_count(session_factory, model)
        for model in (
            Organization,
            User,
            Role,
            Permission,
            Pipeline,
            PipelineStage,
            ModuleToggle,
            Contact,
            Deal,
            EventLog,
            CommunicationThread,
            Communication,
        )
    )


def test_demo_seed_blocked_without_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("SEED_DEMO", raising=False)

    assert not demo_seed_allowed()

    with pytest.raises(SeedBlockedError, match="explicit opt-in"):
        assert_demo_seed_allowed()


def test_demo_seed_blocked_in_production_like_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SEED_DEMO", "true")

    assert not demo_seed_allowed()

    with pytest.raises(SeedBlockedError, match="APP_ENV='production'"):
        assert_demo_seed_allowed()


def test_demo_seed_blocked_in_staging_like_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("SEED_DEMO", "true")

    assert not demo_seed_allowed()

    with pytest.raises(SeedBlockedError, match="APP_ENV='staging'"):
        assert_demo_seed_allowed()


def test_seed_main_is_no_op_without_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("SEED_DEMO", raising=False)

    seed_main()


@requires_test_database
def test_seed_demo_data_is_idempotent(migrated_database: None) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    try:
        with session_factory() as session:
            seed_demo_data(session)

        first_counts = demo_counts(session_factory)

        with session_factory() as session:
            seed_demo_data(session)

        assert demo_counts(session_factory) == first_counts
    finally:
        engine.dispose()


@requires_test_database
def test_seed_demo_data_creates_mvp_baseline_records(migrated_database: None) -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    try:
        with session_factory() as session:
            seed_demo_data(session)

        with session_factory() as session:
            organization = session.scalar(select(Organization).where(Organization.slug == "demo"))
            admin_user = session.scalar(select(User).where(User.email == "admin@example.local"))
            pipeline = session.scalar(select(Pipeline).where(Pipeline.name == "Default sales"))
            stage = session.scalar(select(PipelineStage).where(PipelineStage.name == "New"))
            module_toggle = session.scalar(select(ModuleToggle).where(ModuleToggle.module_key == "crm"))
            contact = session.scalar(select(Contact).where(Contact.email == "baseline.contact@example.local"))
            deal = session.scalar(select(Deal).where(Deal.title == "Baseline Deal"))
            event_log = session.scalar(select(EventLog).where(EventLog.event_type == "seed.baseline"))
            thread = session.scalar(
                select(CommunicationThread).where(CommunicationThread.external_thread_id == "baseline-thread")
            )
            communication = session.scalar(
                select(Communication).where(Communication.external_message_id == "baseline-message")
            )

        assert organization is not None
        assert admin_user is not None
        assert pipeline is not None
        assert stage is not None
        assert module_toggle is not None
        assert contact is not None
        assert deal is not None
        assert event_log is not None
        assert thread is not None
        assert communication is not None
        assert admin_user.organization_id == organization.id
        assert pipeline.organization_id == organization.id
        assert stage.organization_id == organization.id
        assert module_toggle.organization_id == organization.id
        assert contact.organization_id == organization.id
        assert deal.organization_id == organization.id
        assert event_log.organization_id == organization.id
        assert thread.organization_id == organization.id
        assert communication.organization_id == organization.id
        assert deal.stage_id == stage.id
        assert communication.thread_id == thread.id
    finally:
        engine.dispose()
