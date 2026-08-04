from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
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
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        UniqueConstraint("id", "organization_id", name="uq_users_id_org"),
    )

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
        ForeignKeyConstraint(
            ["user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            ondelete="CASCADE",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    refresh_token_jti: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))


class Role(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_roles_org_name"),
        UniqueConstraint("id", "organization_id", name="uq_roles_id_org"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


class Permission(IdMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))


class UserRole(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        ForeignKeyConstraint(
            ["user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["role_id", "organization_id"],
            ["roles.id", "roles.organization_id"],
            ondelete="CASCADE",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)


class RolePermission(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        ForeignKeyConstraint(
            ["role_id", "organization_id"],
            ["roles.id", "roles.organization_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
    )

    role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    permission_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)


class ModuleToggle(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "module_toggles"
    __table_args__ = (UniqueConstraint("organization_id", "module_key", name="uq_module_toggles_org_module"),)

    module_key: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    config: Mapped[dict[str, Any]] = jsonb_column()


class Company(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_companies_id_org"),
        Index("ix_companies_org_name", "organization_id", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    custom_fields: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Contact(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_contacts_id_org"),
        ForeignKeyConstraint(
            ["company_id", "organization_id"],
            ["companies.id", "companies.organization_id"],
            ondelete="RESTRICT",
        ),
        Index("ix_contacts_org_email", "organization_id", "email"),
    )

    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(80))
    custom_fields: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Pipeline(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "pipelines"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_pipelines_org_name"),
        UniqueConstraint("id", "organization_id", name="uq_pipelines_id_org"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class PipelineStage(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("pipeline_id", "name", name="uq_pipeline_stages_pipeline_name"),
        UniqueConstraint("pipeline_id", "position", name="uq_pipeline_stages_pipeline_position"),
        UniqueConstraint("id", "organization_id", name="uq_pipeline_stages_id_org"),
        UniqueConstraint("id", "pipeline_id", name="uq_pipeline_stages_id_pipeline"),
        ForeignKeyConstraint(
            ["pipeline_id", "organization_id"],
            ["pipelines.id", "pipelines.organization_id"],
            ondelete="CASCADE",
        ),
    )

    pipeline_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Deal(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_deals_id_org"),
        ForeignKeyConstraint(
            ["pipeline_id", "organization_id"],
            ["pipelines.id", "pipelines.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["stage_id", "pipeline_id"],
            ["pipeline_stages.id", "pipeline_stages.pipeline_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "organization_id"],
            ["companies.id", "companies.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["contact_id", "organization_id"],
            ["contacts.id", "contacts.organization_id"],
            ondelete="RESTRICT",
        ),
        Index("ix_deals_org_stage", "organization_id", "stage_id"),
    )

    pipeline_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    stage_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    contact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'RUB'"))
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'open'"))
    custom_fields: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class EventLog(IdMixin, OrganizationBoundMixin, Base):
    __tablename__ = "event_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["actor_user_id", "organization_id"],
            ["users.id", "users.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["contact_id", "organization_id"],
            ["contacts.id", "contacts.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "organization_id"],
            ["companies.id", "companies.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["deal_id", "organization_id"],
            ["deals.id", "deals.organization_id"],
            ondelete="RESTRICT",
        ),
        Index("ix_event_logs_org_recorded", "organization_id", "recorded_at"),
    )

    actor_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    contact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    deal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    payload: Mapped[dict[str, Any]] = jsonb_column()
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CommunicationThread(IdMixin, OrganizationBoundMixin, TimestampMixin, Base):
    __tablename__ = "communication_threads"
    __table_args__ = (
        UniqueConstraint("organization_id", "channel_type", "external_thread_id", name="uq_communication_threads_org_external"),
        UniqueConstraint("id", "organization_id", name="uq_communication_threads_id_org"),
        ForeignKeyConstraint(
            ["contact_id", "organization_id"],
            ["contacts.id", "contacts.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["company_id", "organization_id"],
            ["companies.id", "companies.organization_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["deal_id", "organization_id"],
            ["deals.id", "deals.organization_id"],
            ondelete="RESTRICT",
        ),
    )

    contact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    company_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    deal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    channel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    external_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)


class Communication(IdMixin, OrganizationBoundMixin, Base):
    __tablename__ = "communications"
    __table_args__ = (
        UniqueConstraint("thread_id", "external_message_id", name="uq_communications_thread_external_message"),
        ForeignKeyConstraint(
            ["thread_id", "organization_id"],
            ["communication_threads.id", "communication_threads.organization_id"],
            ondelete="CASCADE",
        ),
        Index("ix_communications_thread_occurred", "thread_id", "occurred_at"),
    )

    thread_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(80), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = jsonb_column()
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
