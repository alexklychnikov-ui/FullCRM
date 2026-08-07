from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.service import get_analytics_summary
from app.db.models import Deal, PipelineStage

MAX_TOP_OPEN_DEALS = 8
MAX_STALE_DEALS = 8


@dataclass(frozen=True)
class OrgTopDeal:
    title: str
    stage_name: str
    status: str
    amount: float | None
    currency: str
    days_since_update: int


@dataclass(frozen=True)
class OrgAnalyticsAiContext:
    organization_id: UUID
    summary: dict[str, Any]
    top_open_deals: tuple[OrgTopDeal, ...]
    stale_deals: tuple[OrgTopDeal, ...]


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def build_org_analytics_context(
    session: Session,
    organization_id: UUID,
) -> OrgAnalyticsAiContext:
    summary = get_analytics_summary(session, organization_id)
    stage_names = {
        row[0]: row[1]
        for row in session.execute(
            select(PipelineStage.id, PipelineStage.name).where(
                PipelineStage.organization_id == organization_id
            )
        ).all()
    }

    open_deals = session.scalars(
        select(Deal)
        .where(
            Deal.organization_id == organization_id,
            Deal.status == "open",
        )
        .order_by(Deal.amount.desc().nulls_last(), Deal.updated_at.asc())
        .limit(MAX_TOP_OPEN_DEALS)
    ).all()

    from datetime import UTC, datetime

    now = datetime.now(UTC)

    def _days(deal: Deal) -> int:
        moment = deal.updated_at
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return max((now - moment).days, 0)

    top_open = tuple(
        OrgTopDeal(
            title=deal.title,
            stage_name=stage_names.get(deal.stage_id, "Unknown"),
            status=deal.status,
            amount=_as_float(deal.amount),
            currency=deal.currency,
            days_since_update=_days(deal),
        )
        for deal in open_deals
    )

    stale = tuple(
        OrgTopDeal(
            title=item.title,
            stage_name=item.stage_name,
            status=item.status,
            amount=item.amount,
            currency=item.currency,
            days_since_update=item.days_since_update,
        )
        for item in summary.follow_up.deals[:MAX_STALE_DEALS]
    )

    return OrgAnalyticsAiContext(
        organization_id=organization_id,
        summary=summary.model_dump(mode="json"),
        top_open_deals=top_open,
        stale_deals=stale,
    )


def org_context_to_prompt_payload(context: OrgAnalyticsAiContext) -> dict[str, Any]:
    return {
        "response_language": "ru",
        "scope": "organization_analytics",
        "analytics_summary": context.summary,
        "top_open_deals": [
            {
                "title": item.title,
                "stage": item.stage_name,
                "status": item.status,
                "amount": item.amount,
                "currency": item.currency,
                "days_since_update": item.days_since_update,
            }
            for item in context.top_open_deals
        ],
        "stale_deals": [
            {
                "title": item.title,
                "stage": item.stage_name,
                "status": item.status,
                "amount": item.amount,
                "currency": item.currency,
                "days_since_update": item.days_since_update,
            }
            for item in context.stale_deals
        ],
        "analysis_focus": [
            "общее здоровье pipeline и конверсия",
            "денежный потенциал открытых сделок vs цикл закрытия",
            "риски просрочек и застревания на этапах",
            "перспективы ближайшего периода",
            "план развития бизнеса: приоритеты на 1-2 недели и на месяц",
        ],
    }
