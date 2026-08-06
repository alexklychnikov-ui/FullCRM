from copy import deepcopy
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models import Organization
from app.organizations.schemas import (
    AnalyticsSettingsOut,
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
