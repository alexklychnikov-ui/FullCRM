"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-04 16:07:00 UTC
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def id_column() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )


def organization_id_column() -> sa.Column:
    return sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False)


def timestamp_columns() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def jsonb_column(name: str) -> sa.Column:
    return sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False)


def organization_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "organizations",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        jsonb_column("settings"),
        id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "permissions",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "channel_accounts",
        sa.Column("channel_type", sa.String(length=80), nullable=False),
        sa.Column("external_account_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default=sa.text("'active'"), nullable=False),
        jsonb_column("settings"),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "channel_type", "external_account_id", name="uq_channel_accounts_org_external"),
        organization_fk(),
    )
    op.create_index("ix_channel_accounts_organization_id", "channel_accounts", ["organization_id"])

    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        jsonb_column("custom_fields"),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        organization_fk(),
    )
    op.create_index("ix_companies_organization_id", "companies", ["organization_id"])
    op.create_index("ix_companies_org_name", "companies", ["organization_id", "name"])

    op.create_table(
        "integration_accounts",
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_account_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default=sa.text("'active'"), nullable=False),
        jsonb_column("settings"),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "provider", "external_account_id", name="uq_integration_accounts_org_external"),
        organization_fk(),
    )
    op.create_index("ix_integration_accounts_organization_id", "integration_accounts", ["organization_id"])

    op.create_table(
        "module_toggles",
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        jsonb_column("config"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "module_key", name="uq_module_toggles_org_module"),
        organization_fk(),
    )
    op.create_index("ix_module_toggles_organization_id", "module_toggles", ["organization_id"])

    op.create_table(
        "pipelines",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_pipelines_org_name"),
        organization_fk(),
    )
    op.create_index("ix_pipelines_organization_id", "pipelines", ["organization_id"])

    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name", name="uq_roles_org_name"),
        organization_fk(),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])

    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=120), nullable=False),
        jsonb_column("value"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),
        organization_fk(),
    )
    op.create_index("ix_settings_organization_id", "settings", ["organization_id"])

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        organization_fk(),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    op.create_table(
        "ai_logs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        jsonb_column("metadata"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        id_column(),
        organization_id_column(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_ai_logs_org_created", "ai_logs", ["organization_id", "created_at"])
    op.create_index("ix_ai_logs_organization_id", "ai_logs", ["organization_id"])

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        jsonb_column("diff"),
        jsonb_column("metadata"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        id_column(),
        organization_id_column(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_audit_logs_org_created", "audit_logs", ["organization_id", "created_at"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])

    op.create_table(
        "customers",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        jsonb_column("custom_fields"),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_customers_org_email", "customers", ["organization_id", "email"])
    op.create_index("ix_customers_organization_id", "customers", ["organization_id"])

    op.create_table(
        "pipeline_stages",
        sa.Column("pipeline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Integer(), server_default=sa.text("0"), nullable=False),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pipeline_id", "name", name="uq_pipeline_stages_pipeline_name"),
        sa.UniqueConstraint("pipeline_id", "position", name="uq_pipeline_stages_pipeline_position"),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"], ondelete="CASCADE"),
        organization_fk(),
    )
    op.create_index("ix_pipeline_stages_organization_id", "pipeline_stages", ["organization_id"])

    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        organization_fk(),
    )
    op.create_index("ix_role_permissions_organization_id", "role_permissions", ["organization_id"])

    op.create_table(
        "sync_cursors",
        sa.Column("integration_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource", sa.String(length=120), nullable=False),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_account_id", "resource", name="uq_sync_cursors_account_resource"),
        sa.ForeignKeyConstraint(["integration_account_id"], ["integration_accounts.id"], ondelete="CASCADE"),
        organization_fk(),
    )
    op.create_index("ix_sync_cursors_organization_id", "sync_cursors", ["organization_id"])

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        organization_fk(),
    )
    op.create_index("ix_user_roles_organization_id", "user_roles", ["organization_id"])

    op.create_table(
        "communication_threads",
        sa.Column("channel_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_thread_id", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_account_id", "external_thread_id", name="uq_communication_threads_account_external"),
        sa.ForeignKeyConstraint(["channel_account_id"], ["channel_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_communication_threads_organization_id", "communication_threads", ["organization_id"])

    op.create_table(
        "deals",
        sa.Column("pipeline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'RUB'"), nullable=False),
        sa.Column("status", sa.String(length=40), server_default=sa.text("'open'"), nullable=False),
        jsonb_column("custom_fields"),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["stage_id"], ["pipeline_stages.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_deals_org_stage", "deals", ["organization_id", "stage_id"])
    op.create_index("ix_deals_organization_id", "deals", ["organization_id"])

    op.create_table(
        "ai_recommendations",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), server_default=sa.text("'open'"), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_ai_recommendations_org_status", "ai_recommendations", ["organization_id", "status"])
    op.create_index("ix_ai_recommendations_organization_id", "ai_recommendations", ["organization_id"])

    op.create_table(
        "communications",
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("channel_type", sa.String(length=80), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        jsonb_column("payload"),
        jsonb_column("metadata"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        id_column(),
        organization_id_column(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "external_message_id", name="uq_communications_thread_external_message"),
        sa.ForeignKeyConstraint(["thread_id"], ["communication_threads.id"], ondelete="CASCADE"),
        organization_fk(),
    )
    op.create_index("ix_communications_thread_occurred", "communications", ["thread_id", "occurred_at"])
    op.create_index("ix_communications_organization_id", "communications", ["organization_id"])

    op.create_table(
        "deal_stage_history",
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_stage_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_stage_id"], ["pipeline_stages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_stage_id"], ["pipeline_stages.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_deal_stage_history_organization_id", "deal_stage_history", ["organization_id"])
    op.create_index("ix_deal_stage_history_deal_changed", "deal_stage_history", ["deal_id", "changed_at"])

    op.create_table(
        "events",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        jsonb_column("payload"),
        jsonb_column("metadata"),
        id_column(),
        organization_id_column(),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="SET NULL"),
        organization_fk(),
    )
    op.create_index("ix_events_organization_id", "events", ["organization_id"])
    op.create_index("ix_events_org_starts_at", "events", ["organization_id", "starts_at"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("deal_stage_history")
    op.drop_table("communications")
    op.drop_table("ai_recommendations")
    op.drop_table("deals")
    op.drop_table("communication_threads")
    op.drop_table("user_roles")
    op.drop_table("sync_cursors")
    op.drop_table("role_permissions")
    op.drop_table("pipeline_stages")
    op.drop_table("customers")
    op.drop_table("audit_logs")
    op.drop_table("ai_logs")
    op.drop_table("users")
    op.drop_table("settings")
    op.drop_table("roles")
    op.drop_table("pipelines")
    op.drop_table("module_toggles")
    op.drop_table("integration_accounts")
    op.drop_table("companies")
    op.drop_table("channel_accounts")
    op.drop_table("permissions")
    op.drop_table("organizations")
