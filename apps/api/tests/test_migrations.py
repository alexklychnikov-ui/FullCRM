from os import environ
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for migration integration tests",
)


def alembic_config() -> Config:
    root = Path(__file__).parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    return config


def table_names(database_url: str) -> set[str]:
    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


def foreign_keys_by_table(database_url: str, table_name: str) -> list[dict[str, object]]:
    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            return inspect(connection).get_foreign_keys(table_name)
    finally:
        engine.dispose()


def has_invalid_composite_set_null(database_url: str, table_name: str) -> bool:
    return any(
        foreign_key["options"].get("ondelete") == "SET NULL" and "organization_id" in foreign_key["constrained_columns"]
        for foreign_key in foreign_keys_by_table(database_url, table_name)
    )


def reset_public_schema(database_url: str) -> None:
    engine = create_engine(database_url)

    try:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    finally:
        engine.dispose()


def test_migration_cycle_upgrade_seed_downgrade_upgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    config = alembic_config()
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("SEED_DEMO", "true")
    reset_public_schema(TEST_DATABASE_URL)

    try:
        command.upgrade(config, "head")
        upgraded_tables = table_names(TEST_DATABASE_URL)
        assert {"organizations", "contacts", "deals", "event_logs", "communications", "auth_sessions"} <= upgraded_tables
        auth_session_foreign_keys = foreign_keys_by_table(TEST_DATABASE_URL, "auth_sessions")
        assert any(
            foreign_key["referred_table"] == "users"
            and foreign_key["constrained_columns"] == ["user_id", "organization_id"]
            and foreign_key["referred_columns"] == ["id", "organization_id"]
            for foreign_key in auth_session_foreign_keys
        )
        for table_name in ("contacts", "deals", "event_logs", "communication_threads"):
            assert not has_invalid_composite_set_null(TEST_DATABASE_URL, table_name)

        from app.db.seed import main as seed_main

        seed_main()
        seeded_tables = table_names(TEST_DATABASE_URL)
        assert seeded_tables == upgraded_tables

        command.downgrade(config, "base")
        assert table_names(TEST_DATABASE_URL) == {"alembic_version"}

        command.upgrade(config, "head")
        assert {"organizations", "contacts", "deals", "event_logs", "communications", "auth_sessions"} <= table_names(
            TEST_DATABASE_URL
        )
    finally:
        reset_public_schema(TEST_DATABASE_URL)
