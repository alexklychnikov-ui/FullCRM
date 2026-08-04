from pathlib import Path

from sqlalchemy.dialects.postgresql import JSONB

from app.db import models as db_models
from app.db.base import metadata
from app.db.policies import (
    AI_LOG_REDACTION_POLICY,
    JSONB_SENSITIVE_DATA_POLICY,
    POLICY_JSONB_COLUMNS,
    TABLES_REQUIRING_APP_TENANT_GUARDS,
    TENANT_CONSISTENCY_POLICY,
    TOKEN_STORAGE_POLICY,
)

_ = db_models


def jsonb_columns() -> set[str]:
    return {
        f"{table.name}.{column.name}"
        for table in metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, JSONB)
    }


def tenant_child_reference_tables() -> set[str]:
    return {
        table.name
        for table in metadata.tables.values()
        if "organization_id" in table.columns
        and any(foreign_key.parent.name != "organization_id" for foreign_key in table.foreign_keys)
    }


def test_migration_is_static_and_does_not_import_live_metadata() -> None:
    migration = Path(__file__).parents[1] / "migrations" / "versions" / "0001_initial.py"
    migration_text = migration.read_text(encoding="utf-8")

    assert "app.db" not in migration_text
    assert "create_all" not in migration_text
    assert "drop_all" not in migration_text
    assert "op.create_table" in migration_text
    assert "op.drop_table" in migration_text


def test_jsonb_sensitive_data_policy_covers_schema_jsonb_columns() -> None:
    policy_text = " ".join(
        (
            JSONB_SENSITIVE_DATA_POLICY,
            TOKEN_STORAGE_POLICY,
            AI_LOG_REDACTION_POLICY,
        )
    ).lower()

    assert jsonb_columns() == set(POLICY_JSONB_COLUMNS)
    assert "raw secrets" in policy_text
    assert "raw tokens" in policy_text
    assert "env reference" in policy_text
    assert "encrypted secret reference" in policy_text
    assert "redacted" in policy_text


def test_tenant_consistency_policy_covers_child_reference_tables() -> None:
    policy_text = TENANT_CONSISTENCY_POLICY.lower()

    assert tenant_child_reference_tables() == set(TABLES_REQUIRING_APP_TENANT_GUARDS)
    assert "service-layer ownership guards" in policy_text
    assert "i3-i5" in policy_text
    assert "rls" in policy_text
    assert "composite fks" in policy_text
