from collections.abc import Iterable
from datetime import UTC, datetime
from os import getenv
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.db.models import (
    Communication,
    CommunicationThread,
    Company,
    Contact,
    Deal,
    EventLog,
    ModuleToggle,
    Organization,
    Permission,
    Pipeline,
    PipelineStage,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.db.session import create_db_engine, create_session_factory


ModelT = TypeVar("ModelT")
DISABLED_PASSWORD_HASH = "disabled_until_auth_i3"
SEED_DEMO_OPT_IN_ENV = "SEED_DEMO"
SEED_ADMIN_PASSWORD_ENV = "SEED_ADMIN_PASSWORD"
DEVELOPMENT_LIKE_ENVS = frozenset({"local", "development", "dev", "test"})
PRODUCTION_LIKE_ENVS = frozenset({"production", "prod", "staging", "stage"})


class SeedBlockedError(RuntimeError):
    """Raised when demo seed is invoked outside an allowed local/dev context."""


def normalize_app_env() -> str:
    return getenv("APP_ENV", "local").strip().lower() or "local"


def is_development_like_env(app_env: str | None = None) -> bool:
    env = normalize_app_env() if app_env is None else app_env.strip().lower()

    if env in PRODUCTION_LIKE_ENVS:
        return False

    return env in DEVELOPMENT_LIKE_ENVS


def is_demo_seed_opted_in() -> bool:
    raw = getenv(SEED_DEMO_OPT_IN_ENV)

    if raw is None:
        return False

    return raw.strip().lower() in {"1", "true", "yes", "on"}


def demo_seed_allowed() -> bool:
    return is_development_like_env() and is_demo_seed_opted_in()


def assert_demo_seed_allowed() -> None:
    if not is_development_like_env():
        raise SeedBlockedError(
            f"Demo seed is disabled for APP_ENV={normalize_app_env()!r}; "
            "only local/development-like environments are allowed."
        )

    if not is_demo_seed_opted_in():
        raise SeedBlockedError(
            f"Demo seed requires explicit opt-in via {SEED_DEMO_OPT_IN_ENV}=true."
        )

DEFAULT_PERMISSIONS = (
    ("crm.read", "Read CRM records"),
    ("crm.write", "Create and update CRM records"),
    ("communications.read", "Read organization communications"),
    ("communications.write", "Create communications and trigger integrations"),
    ("ai.read", "Read AI advisory insights"),
    ("analytics.read", "Read analytics dashboards"),
    ("admin.manage", "Manage organization users and access"),
)
DEFAULT_ROLE_DEFINITIONS = (
    (
        "admin",
        "Organization administrator",
        (
            "crm.read",
            "crm.write",
            "communications.read",
            "communications.write",
            "ai.read",
            "analytics.read",
            "admin.manage",
        ),
    ),
    (
        "manager",
        "Sales manager",
        (
            "crm.read",
            "crm.write",
            "communications.read",
            "communications.write",
            "ai.read",
            "analytics.read",
        ),
    ),
    (
        "analyst",
        "Business analyst",
        (
            "crm.read",
            "communications.read",
            "ai.read",
            "analytics.read",
        ),
    ),
)
DEFAULT_STAGES = (
    ("New", 10, 10),
    ("Qualified", 20, 40),
    ("Won", 30, 100),
)
DEFAULT_MODULES = ("crm", "communications", "ai", "analytics")


def get_or_create(
    session: Session,
    model: type[ModelT],
    filters: dict[str, Any],
    defaults: dict[str, Any] | None = None,
) -> ModelT:
    conditions = [getattr(model, key) == value for key, value in filters.items()]
    instance = session.scalar(select(model).where(*conditions))

    if instance is not None:
        return instance

    instance = model(**filters, **(defaults or {}))
    session.add(instance)
    session.flush()
    return instance


def ensure_permissions(session: Session) -> dict[str, Permission]:
    permissions: dict[str, Permission] = {}

    for key, description in DEFAULT_PERMISSIONS:
        permissions[key] = get_or_create(
            session,
            Permission,
            {"key": key},
            {"description": description},
        )

    return permissions


def ensure_role_permissions(
    session: Session,
    organization: Organization,
    role: Role,
    permissions: Iterable[Permission],
) -> None:
    for permission in permissions:
        get_or_create(
            session,
            RolePermission,
            {
                "organization_id": organization.id,
                "role_id": role.id,
                "permission_id": permission.id,
            },
        )


def ensure_user_role(session: Session, organization: Organization, user: User, role: Role) -> None:
    get_or_create(
        session,
        UserRole,
        {
            "organization_id": organization.id,
            "user_id": user.id,
            "role_id": role.id,
        },
    )


def ensure_default_roles(session: Session, organization: Organization) -> dict[str, Role]:
    permissions = ensure_permissions(session)
    roles: dict[str, Role] = {}

    for name, description, permission_keys in DEFAULT_ROLE_DEFINITIONS:
        role = get_or_create(
            session,
            Role,
            {"organization_id": organization.id, "name": name},
            {"description": description},
        )
        ensure_role_permissions(
            session,
            organization,
            role,
            [permissions[key] for key in permission_keys],
        )
        roles[name] = role

    return roles


def apply_seed_password(user: User, env_name: str) -> None:
    password = getenv(env_name)

    if password and user.password_hash == DISABLED_PASSWORD_HASH:
        user.password_hash = hash_password(password)


def ensure_default_pipeline(session: Session, organization: Organization) -> Pipeline:
    pipeline = get_or_create(
        session,
        Pipeline,
        {"organization_id": organization.id, "name": "Default sales"},
        {"is_default": True},
    )

    for name, position, probability in DEFAULT_STAGES:
        get_or_create(
            session,
            PipelineStage,
            {"pipeline_id": pipeline.id, "name": name},
            {
                "organization_id": organization.id,
                "position": position,
                "probability": probability,
            },
        )

    return pipeline


def ensure_baseline_records(
    session: Session,
    organization: Organization,
    owner: User,
    pipeline: Pipeline,
) -> None:
    stage = session.scalar(
        select(PipelineStage).where(
            PipelineStage.pipeline_id == pipeline.id,
            PipelineStage.organization_id == organization.id,
            PipelineStage.name == "New",
        )
    )
    assert stage is not None

    company = get_or_create(
        session,
        Company,
        {"organization_id": organization.id, "name": "Baseline Company"},
        {"domain": "baseline.local"},
    )
    contact = get_or_create(
        session,
        Contact,
        {"organization_id": organization.id, "email": "baseline.contact@example.local"},
        {
            "company_id": company.id,
            "full_name": "Baseline Contact",
        },
    )
    deal = get_or_create(
        session,
        Deal,
        {"organization_id": organization.id, "title": "Baseline Deal"},
        {
            "pipeline_id": pipeline.id,
            "stage_id": stage.id,
            "company_id": company.id,
            "contact_id": contact.id,
            "amount": 1000,
        },
    )
    get_or_create(
        session,
        EventLog,
        {
            "organization_id": organization.id,
            "event_type": "seed.baseline",
            "entity_type": "deal",
            "entity_id": deal.id,
        },
        {
            "actor_user_id": owner.id,
            "deal_id": deal.id,
            "payload": {"seed": True},
        },
    )
    thread = get_or_create(
        session,
        CommunicationThread,
        {
            "organization_id": organization.id,
            "channel_type": "email",
            "external_thread_id": "baseline-thread",
        },
        {
            "contact_id": contact.id,
            "subject": "Baseline thread",
        },
    )
    get_or_create(
        session,
        Communication,
        {
            "organization_id": organization.id,
            "thread_id": thread.id,
            "external_message_id": "baseline-message",
        },
        {
            "direction": "inbound",
            "channel_type": "email",
            "payload": {"seed": True},
            "occurred_at": datetime(2026, 8, 4, 9, 0, tzinfo=UTC),
        },
    )


def seed_demo_data(session: Session) -> None:
    assert_demo_seed_allowed()

    organization = get_or_create(
        session,
        Organization,
        {"slug": "demo"},
        {"name": "Baseline Organization"},
    )
    roles = ensure_default_roles(session, organization)
    admin_role = roles["admin"]
    admin_user = get_or_create(
        session,
        User,
        {"organization_id": organization.id, "email": "admin@example.local"},
        {
            "full_name": "Baseline Admin",
            "password_hash": DISABLED_PASSWORD_HASH,
        },
    )

    apply_seed_password(admin_user, SEED_ADMIN_PASSWORD_ENV)
    ensure_user_role(session, organization, admin_user, admin_role)
    pipeline = ensure_default_pipeline(session, organization)

    for module_key in DEFAULT_MODULES:
        get_or_create(
            session,
            ModuleToggle,
            {"organization_id": organization.id, "module_key": module_key},
            {"enabled": True},
        )

    ensure_baseline_records(session, organization, admin_user, pipeline)
    session.commit()


def main() -> None:
    if not demo_seed_allowed():
        return

    engine = create_db_engine()
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        seed_demo_data(session)


if __name__ == "__main__":
    main()
