from copy import deepcopy
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from sqlalchemy import select

from app.db.models import ModuleToggle, Organization
from app.db.seed import DEFAULT_MODULES
from app.organizations.schemas import (
    AnalyticsSettingsOut,
    OrganizationModuleOut,
    OrganizationModulesOut,
    OrganizationModulesPatch,
    OrganizationSettingsOut,
    OrganizationSettingsPatch,
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
