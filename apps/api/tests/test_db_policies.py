from pathlib import Path

from sqlalchemy.dialects.postgresql import JSONB

from app.db import models as db_models
from app.db.base import metadata
from app.db.policies import (
    JSONB_SENSITIVE_DATA_POLICY,
    TENANT_OWNERSHIP_POLICY,
)

_ = db_models


ALLOWED_JSONB_COLUMN_NAMES = {"config", "custom_fields", "metadata", "payload", "settings"}


def jsonb_columns() -> set[tuple[str, str]]:
    return {
        (table.name, column.name)
        for table in metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, JSONB)
    }


def tenant_bound_tables() -> set[str]:
    return {
        table.name
        for table in metadata.tables.values()
        if "organization_id" in table.columns
    }


def tenant_child_reference_tables() -> set[str]:
    tenant_tables = tenant_bound_tables()
    return {
        table.name
        for table in metadata.tables.values()
        if table.name in tenant_tables
        and any(
            foreign_key.column.table.name in tenant_tables and foreign_key.parent.name != "organization_id"
            for foreign_key in table.foreign_keys
        )
    }


def composite_tenant_set_null_tables() -> set[str]:
    return {
        table.name
        for table in metadata.tables.values()
        for constraint in table.foreign_key_constraints
        if len(constraint.columns) > 1
        and "organization_id" in constraint.columns.keys()
        and constraint.ondelete == "SET NULL"
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
    policy_text = JSONB_SENSITIVE_DATA_POLICY.lower()

    assert {column_name for _, column_name in jsonb_columns()} <= ALLOWED_JSONB_COLUMN_NAMES
    assert "raw secrets" in policy_text
    assert "raw tokens" in policy_text
    assert "redacted" in policy_text
    assert "baseline checks" in policy_text


def test_tenant_ownership_policy_covers_composite_tenant_fk_tables() -> None:
    policy_text = TENANT_OWNERSHIP_POLICY.lower()

    for table_name in tenant_child_reference_tables():
        table = metadata.tables[table_name]
        assert any(
            len(constraint.columns) > 1 and "organization_id" in constraint.columns.keys()
            for constraint in table.foreign_key_constraints
        )
    assert "organization_id" in policy_text
    assert "composite foreign keys" in policy_text
    assert "database layer" in policy_text


def test_composite_tenant_foreign_keys_do_not_use_set_null() -> None:
    assert composite_tenant_set_null_tables() == set()
