"""Production-safe first admin bootstrap (no demo CRM data)."""

from os import getenv

from sqlalchemy import func, select

from app.auth.passwords import hash_password
from app.db.models import ModuleToggle, Organization, Role, User
from app.db.seed import (
    DEFAULT_MODULES,
    ensure_permissions,
    ensure_role_permissions,
    ensure_user_role,
    get_or_create,
)
from app.db.session import create_db_engine, create_session_factory

BOOTSTRAP_OPT_IN_ENV = "BOOTSTRAP_ADMIN"
BOOTSTRAP_CONFIRM_ENV = "BOOTSTRAP_CONFIRM"
BOOTSTRAP_TOKEN_ENV = "BOOTSTRAP_ADMIN_TOKEN"
BOOTSTRAP_EMAIL_ENV = "BOOTSTRAP_ADMIN_EMAIL"
BOOTSTRAP_PASSWORD_ENV = "BOOTSTRAP_ADMIN_PASSWORD"
BOOTSTRAP_ORG_SLUG_ENV = "BOOTSTRAP_ORG_SLUG"
BOOTSTRAP_ORG_NAME_ENV = "BOOTSTRAP_ORG_NAME"
REQUIRED_CONFIRM = "yes"


class BootstrapError(RuntimeError):
    """Raised when production bootstrap preconditions are not met."""


def _truthy(name: str) -> bool:
    raw = getenv(name)
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def assert_bootstrap_allowed() -> None:
    if not _truthy(BOOTSTRAP_OPT_IN_ENV):
        raise BootstrapError(
            f"Production bootstrap requires explicit opt-in via {BOOTSTRAP_OPT_IN_ENV}=true."
        )

    token = getenv(BOOTSTRAP_TOKEN_ENV)
    confirm = getenv(BOOTSTRAP_CONFIRM_ENV, "").strip().lower()
    if token:
        supplied = getenv("BOOTSTRAP_SUPPLIED_TOKEN", "").strip()
        if not supplied or supplied != token.strip():
            raise BootstrapError(
                f"Production bootstrap requires matching {BOOTSTRAP_TOKEN_ENV} "
                f"via BOOTSTRAP_SUPPLIED_TOKEN."
            )
    elif confirm != REQUIRED_CONFIRM:
        raise BootstrapError(
            f"Production bootstrap requires {BOOTSTRAP_CONFIRM_ENV}=yes "
            f"or a valid {BOOTSTRAP_TOKEN_ENV}."
        )

    email = getenv(BOOTSTRAP_EMAIL_ENV, "").strip()
    password = getenv(BOOTSTRAP_PASSWORD_ENV, "")
    if not email:
        raise BootstrapError(f"{BOOTSTRAP_EMAIL_ENV} is required.")
    if not password:
        raise BootstrapError(f"{BOOTSTRAP_PASSWORD_ENV} is required.")


def bootstrap_prod_admin(session) -> User:
    assert_bootstrap_allowed()

    existing_users = session.scalar(select(func.count()).select_from(User)) or 0
    if existing_users > 0:
        raise BootstrapError(
            "Bootstrap refused: users already exist. Use admin UI or reset DB."
        )

    email = getenv(BOOTSTRAP_EMAIL_ENV, "").strip()
    password = getenv(BOOTSTRAP_PASSWORD_ENV, "")
    org_slug = getenv(BOOTSTRAP_ORG_SLUG_ENV, "main").strip() or "main"
    org_name = getenv(BOOTSTRAP_ORG_NAME_ENV, "FullCRM").strip() or "FullCRM"

    organization = get_or_create(
        session,
        Organization,
        {"slug": org_slug},
        {"name": org_name},
    )
    permissions = ensure_permissions(session)
    admin_role = get_or_create(
        session,
        Role,
        {"organization_id": organization.id, "name": "admin"},
        {"description": "Organization administrator"},
    )
    admin_user = get_or_create(
        session,
        User,
        {"organization_id": organization.id, "email": email},
        {
            "full_name": "Administrator",
            "password_hash": hash_password(password),
        },
    )

    ensure_role_permissions(session, organization, admin_role, permissions.values())
    ensure_user_role(session, organization, admin_user, admin_role)

    for module_key in DEFAULT_MODULES:
        get_or_create(
            session,
            ModuleToggle,
            {"organization_id": organization.id, "module_key": module_key},
            {"enabled": True},
        )

    session.commit()
    return admin_user


def main() -> None:
    engine = create_db_engine()
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        user = bootstrap_prod_admin(session)
        print(f"Bootstrap complete for {user.email}")


if __name__ == "__main__":
    main()
