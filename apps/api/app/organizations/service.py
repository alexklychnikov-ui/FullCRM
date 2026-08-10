from copy import deepcopy
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.auth.passwords import hash_password
from app.auth.sessions import revoke_all_user_sessions
from app.db.models import ModuleToggle, Organization, Role, User, UserRole
from app.db.seed import DEFAULT_MODULES, ensure_default_roles
from app.organizations.schemas import (
    AnalyticsSettingsOut,
    OrganizationModuleOut,
    OrganizationModulesOut,
    OrganizationModulesPatch,
    OrganizationRoleOut,
    OrganizationRolesOut,
    OrganizationSettingsOut,
    OrganizationSettingsPatch,
    OrganizationUserCreate,
    OrganizationUserOut,
    OrganizationUserPatch,
    OrganizationUserRolesPut,
    OrganizationUsersOut,
)

DEFAULT_STALE_DEAL_DAYS = 7
DEFAULT_ACTIVITY_WINDOW_DAYS = 7


def _coerce_days(value: Any, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    if value < 1 or value > 365:
        return default
    return value


def resolve_analytics_settings(raw_settings: dict[str, Any] | None) -> AnalyticsSettingsOut:
    analytics = (raw_settings or {}).get("analytics")
    if not isinstance(analytics, dict):
        analytics = {}

    return AnalyticsSettingsOut(
        stale_deal_days=_coerce_days(analytics.get("stale_deal_days"), DEFAULT_STALE_DEAL_DAYS),
        activity_window_days=_coerce_days(
            analytics.get("activity_window_days"),
            DEFAULT_ACTIVITY_WINDOW_DAYS,
        ),
    )


def settings_to_out(raw_settings: dict[str, Any] | None) -> OrganizationSettingsOut:
    return OrganizationSettingsOut(analytics=resolve_analytics_settings(raw_settings))


def get_organization_or_404(session: Session, organization_id: UUID) -> Organization:
    organization = session.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


def get_my_settings(session: Session, organization_id: UUID) -> OrganizationSettingsOut:
    organization = get_organization_or_404(session, organization_id)
    return settings_to_out(organization.settings)


def patch_my_settings(
    session: Session,
    organization_id: UUID,
    payload: OrganizationSettingsPatch,
) -> OrganizationSettingsOut:
    organization = get_organization_or_404(session, organization_id)
    merged = deepcopy(organization.settings) if isinstance(organization.settings, dict) else {}

    updates = payload.model_dump(exclude_unset=True)
    analytics_updates = updates.get("analytics")
    if analytics_updates:
        current_analytics = merged.get("analytics")
        if not isinstance(current_analytics, dict):
            current_analytics = {}
        else:
            current_analytics = dict(current_analytics)
        current_analytics.update(analytics_updates)
        merged["analytics"] = current_analytics

    organization.settings = merged
    flag_modified(organization, "settings")
    session.commit()
    session.refresh(organization)
    return settings_to_out(organization.settings)


def get_my_modules(session: Session, organization_id: UUID) -> OrganizationModulesOut:
    get_organization_or_404(session, organization_id)
    toggles = session.scalars(
        select(ModuleToggle).where(ModuleToggle.organization_id == organization_id)
    ).all()
    enabled_by_key = {item.module_key: item.enabled for item in toggles}

    return OrganizationModulesOut(
        modules=[
            OrganizationModuleOut(
                module_key=module_key,
                enabled=enabled_by_key.get(module_key, False),
            )
            for module_key in DEFAULT_MODULES
        ]
    )


def patch_my_modules(
    session: Session,
    organization_id: UUID,
    payload: OrganizationModulesPatch,
) -> OrganizationModulesOut:
    get_organization_or_404(session, organization_id)
    known = set(DEFAULT_MODULES)

    for item in payload.modules:
        if item.module_key not in known:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown module_key: {item.module_key}",
            )
        if item.module_key == "crm" and not item.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CRM module cannot be disabled",
            )

    for item in payload.modules:
        toggle = session.scalar(
            select(ModuleToggle).where(
                ModuleToggle.organization_id == organization_id,
                ModuleToggle.module_key == item.module_key,
            )
        )
        if toggle is None:
            toggle = ModuleToggle(
                organization_id=organization_id,
                module_key=item.module_key,
                enabled=item.enabled,
            )
            session.add(toggle)
        else:
            toggle.enabled = item.enabled

    session.commit()
    return get_my_modules(session, organization_id)


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email",
        )
    return normalized


def _user_role_names(session: Session, user: User) -> list[str]:
    return sorted(
        session.scalars(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user.id,
                UserRole.organization_id == user.organization_id,
                Role.organization_id == user.organization_id,
            )
        ).all()
    )


def _user_to_out(session: Session, user: User) -> OrganizationUserOut:
    return OrganizationUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=_user_role_names(session, user),
        created_at=user.created_at,
    )


def _count_active_admins(session: Session, organization_id: UUID) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.organization_id == organization_id,
                User.is_active.is_(True),
                UserRole.organization_id == organization_id,
                Role.organization_id == organization_id,
                Role.name == "admin",
            )
        )
        or 0
    )


def _resolve_org_roles(session: Session, organization_id: UUID, role_names: list[str]) -> list[Role]:
    unique_names = list(dict.fromkeys(role_names))
    roles = session.scalars(
        select(Role).where(
            Role.organization_id == organization_id,
            Role.name.in_(unique_names),
        )
    ).all()
    found = {role.name for role in roles}
    missing = [name for name in unique_names if name not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown roles: {', '.join(missing)}",
        )
    by_name = {role.name: role for role in roles}
    return [by_name[name] for name in unique_names]


def _get_org_user_or_404(session: Session, organization_id: UUID, user_id: UUID) -> User:
    user = session.scalar(
        select(User).where(
            User.id == user_id,
            User.organization_id == organization_id,
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def ensure_org_default_roles(session: Session, organization_id: UUID) -> dict[str, Role]:
    organization = get_organization_or_404(session, organization_id)
    return ensure_default_roles(session, organization)


def list_my_roles(session: Session, organization_id: UUID) -> OrganizationRolesOut:
    roles_by_name = ensure_org_default_roles(session, organization_id)
    session.commit()
    roles = sorted(roles_by_name.values(), key=lambda role: role.name)
    return OrganizationRolesOut(
        roles=[
            OrganizationRoleOut(id=role.id, name=role.name, description=role.description)
            for role in roles
        ]
    )


def list_my_users(session: Session, organization_id: UUID) -> OrganizationUsersOut:
    ensure_org_default_roles(session, organization_id)
    session.commit()
    users = session.scalars(
        select(User)
        .where(User.organization_id == organization_id)
        .order_by(User.email.asc())
    ).all()
    return OrganizationUsersOut(users=[_user_to_out(session, user) for user in users])


def create_my_user(
    session: Session,
    organization_id: UUID,
    payload: OrganizationUserCreate,
) -> OrganizationUserOut:
    ensure_org_default_roles(session, organization_id)
    email = _normalize_email(payload.email)
    roles = _resolve_org_roles(session, organization_id, payload.roles)

    existing = session.scalar(
        select(User).where(
            User.organization_id == organization_id,
            User.email == email,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = User(
        organization_id=organization_id,
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    session.flush()

    for role in roles:
        session.add(
            UserRole(
                organization_id=organization_id,
                user_id=user.id,
                role_id=role.id,
            )
        )

    session.commit()
    session.refresh(user)
    return _user_to_out(session, user)


def patch_my_user(
    session: Session,
    organization_id: UUID,
    user_id: UUID,
    payload: OrganizationUserPatch,
    actor_user_id: UUID,
) -> OrganizationUserOut:
    ensure_org_default_roles(session, organization_id)
    user = _get_org_user_or_404(session, organization_id, user_id)
    updates = payload.model_dump(exclude_unset=True)

    if "is_active" in updates and updates["is_active"] is False:
        if user.id == actor_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )
        if user.is_active and "admin" in _user_role_names(session, user):
            if _count_active_admins(session, organization_id) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active admin",
                )
        user.is_active = False
        revoke_all_user_sessions(session, user.id, organization_id)
    elif "is_active" in updates and updates["is_active"] is True:
        user.is_active = True

    if "full_name" in updates and updates["full_name"] is not None:
        user.full_name = updates["full_name"].strip()

    if "password" in updates and updates["password"] is not None:
        user.password_hash = hash_password(updates["password"])
        revoke_all_user_sessions(session, user.id, organization_id)

    session.commit()
    session.refresh(user)
    return _user_to_out(session, user)


def put_my_user_roles(
    session: Session,
    organization_id: UUID,
    user_id: UUID,
    payload: OrganizationUserRolesPut,
    actor_user_id: UUID,
) -> OrganizationUserOut:
    ensure_org_default_roles(session, organization_id)
    user = _get_org_user_or_404(session, organization_id, user_id)
    roles = _resolve_org_roles(session, organization_id, payload.roles)
    new_names = {role.name for role in roles}
    current_names = set(_user_role_names(session, user))

    if (
        user.is_active
        and "admin" in current_names
        and "admin" not in new_names
        and _count_active_admins(session, organization_id) <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin role from the last active admin",
        )

    session.execute(
        delete(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.organization_id == organization_id,
        )
    )
    for role in roles:
        session.add(
            UserRole(
                organization_id=organization_id,
                user_id=user.id,
                role_id=role.id,
            )
        )

    session.commit()
    session.refresh(user)
    return _user_to_out(session, user)
