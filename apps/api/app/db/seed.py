from collections.abc import Iterable
from os import getenv
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.db.models import (
    ModuleToggle,
    Organization,
    Permission,
    Pipeline,
    PipelineStage,
    Role,
    RolePermission,
    Setting,
    User,
    UserRole,
)
from app.db.session import create_db_engine, create_session_factory


ModelT = TypeVar("ModelT")
DISABLED_PASSWORD_HASH = "disabled_until_auth_i3"
SEED_ADMIN_PASSWORD_ENV = "SEED_ADMIN_PASSWORD"
SEED_MANAGER_PASSWORD_ENV = "SEED_MANAGER_PASSWORD"

DEFAULT_PERMISSIONS = (
    ("crm.read", "Read CRM records"),
    ("crm.write", "Create and update CRM records"),
    ("settings.read", "Read organization settings"),
    ("settings.write", "Update organization settings"),
    ("admin.manage", "Manage organization users and access"),
)
DEFAULT_STAGES = (
    ("New", 10, 10),
    ("Qualified", 20, 30),
    ("Proposal", 30, 60),
    ("Won", 40, 100),
    ("Lost", 50, 0),
)
DEFAULT_MODULES = ("crm", "communications", "ai")


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


def seed_demo_data(session: Session) -> None:
    organization = get_or_create(
        session,
        Organization,
        {"slug": "demo"},
        {"name": "Demo Organization"},
    )
    permissions = ensure_permissions(session)
    admin_role = get_or_create(
        session,
        Role,
        {"organization_id": organization.id, "name": "admin"},
        {"description": "Full demo organization access"},
    )
    manager_role = get_or_create(
        session,
        Role,
        {"organization_id": organization.id, "name": "manager"},
        {"description": "CRM manager access"},
    )
    admin_user = get_or_create(
        session,
        User,
        {"organization_id": organization.id, "email": "admin@example.local"},
        {
            "full_name": "Demo Admin",
            "password_hash": DISABLED_PASSWORD_HASH,
        },
    )
    manager_user = get_or_create(
        session,
        User,
        {"organization_id": organization.id, "email": "manager@example.local"},
        {
            "full_name": "Demo Manager",
            "password_hash": DISABLED_PASSWORD_HASH,
        },
    )

    ensure_role_permissions(session, organization, admin_role, permissions.values())
    ensure_role_permissions(
        session,
        organization,
        manager_role,
        (
            permissions["crm.read"],
            permissions["crm.write"],
            permissions["settings.read"],
        ),
    )
    apply_seed_password(admin_user, SEED_ADMIN_PASSWORD_ENV)
    apply_seed_password(manager_user, SEED_MANAGER_PASSWORD_ENV)
    ensure_user_role(session, organization, admin_user, admin_role)
    ensure_user_role(session, organization, manager_user, manager_role)
    ensure_default_pipeline(session, organization)

    for module_key in DEFAULT_MODULES:
        get_or_create(
            session,
            ModuleToggle,
            {"organization_id": organization.id, "module_key": module_key},
            {"enabled": True},
        )

    get_or_create(
        session,
        Setting,
        {"organization_id": organization.id, "key": "locale"},
        {"value": {"default": "ru"}},
    )
    session.commit()


def main() -> None:
    engine = create_db_engine()
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        seed_demo_data(session)


if __name__ == "__main__":
    main()
