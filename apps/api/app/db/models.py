from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def jsonb_column() -> Any:
    return mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class IdMixin:
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OrganizationBoundMixin:
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class Organization(IdMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    settings: Mapped[dict[str, Any]] = jsonb_column()


class User(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_users_org_email"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class AuthSession(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint("refresh_token_hash", name="uq_auth_sessions_refresh_token_hash"),
        UniqueConstraint("refresh_token_jti", name="uq_auth_sessions_refresh_token_jti"),
        Index("ix_auth_sessions_user_active", "user_id", "revoked_at", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    refresh_token_jti: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))


class Role(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_roles_org_name"),)

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


class Permission(IdMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))


class UserRole(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),)

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)


class RolePermission(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),)

    role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )


class Setting(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),)

    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[dict[str, Any]] = jsonb_column()


class ModuleToggle(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "module_toggles"
    __table_args__ = (UniqueConstraint("organization_id", "module_key", name="uq_module_toggles_org_module"),)

    module_key: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    config: Mapped[dict[str, Any]] = jsonb_column()


class Company(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (Index("ix_companies_org_name", "organization_id", "name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    custom_fields: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Customer(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (Index("ix_customers_org_email", "organization_id", "email"),)

    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(80))
    custom_fields: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Pipeline(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "pipelines"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_pipelines_org_name"),)

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class PipelineStage(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("pipeline_id", "name", name="uq_pipeline_stages_pipeline_name"),
        UniqueConstraint("pipeline_id", "position", name="uq_pipeline_stages_pipeline_position"),
    )

    pipeline_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Deal(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (Index("ix_deals_org_stage", "organization_id", "stage_id"),)

    pipeline_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="RESTRICT"), nullable=False)
    stage_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), nullable=False)
    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    customer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'RUB'"))
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'open'"))
    custom_fields: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class DealStageHistory(IdMixin, OrganizationBoundMixin, Base):
    __tablename__ = "deal_stage_history"
    __table_args__ = (Index("ix_deal_stage_history_deal_changed", "deal_id", "changed_at"),)

    deal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    from_stage_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pipeline_stages.id", ondelete="SET NULL"))
    to_stage_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), nullable=False)
    changed_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Event(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (Index("ix_events_org_starts_at", "organization_id", "starts_at"),)

    customer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"))
    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    deal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class AuditLog(IdMixin, OrganizationBoundMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_org_created", "organization_id", "created_at"),)

    actor_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    diff: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ChannelAccount(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "channel_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "channel_type", "external_account_id", name="uq_channel_accounts_org_external"),
    )

    channel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'active'"))
    settings: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class CommunicationThread(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "communication_threads"
    __table_args__ = (
        UniqueConstraint("channel_account_id", "external_thread_id", name="uq_communication_threads_account_external"),
    )

    channel_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("channel_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"))
    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    external_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Communication(IdMixin, OrganizationBoundMixin, Base):
    __tablename__ = "communications"
    __table_args__ = (
        UniqueConstraint("thread_id", "external_message_id", name="uq_communications_thread_external_message"),
        Index("ix_communications_thread_occurred", "thread_id", "occurred_at"),
    )

    thread_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("communication_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiLog(IdMixin, OrganizationBoundMixin, Base):
    __tablename__ = "ai_logs"
    __table_args__ = (Index("ix_ai_logs_org_created", "organization_id", "created_at"),)

    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AiRecommendation(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "ai_recommendations"
    __table_args__ = (Index("ix_ai_recommendations_org_status", "organization_id", "status"),)

    customer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"))
    deal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'open'"))
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class IntegrationAccount(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "integration_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider", "external_account_id", name="uq_integration_accounts_org_external"),
    )

    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'active'"))
    settings: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class SyncCursor(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "sync_cursors"
    __table_args__ = (UniqueConstraint("integration_account_id", "resource", name="uq_sync_cursors_account_resource"),)

    integration_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("integration_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource: Mapped[str] = mapped_column(String(120), nullable=False)
    cursor: Mapped[str | None] = mapped_column(Text)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
