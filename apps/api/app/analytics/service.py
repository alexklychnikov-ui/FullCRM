from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    ActivityOut,
    AnalyticsSummaryOut,
    ConversionOut,
    CycleOut,
    FollowUpDealOut,
    FollowUpOut,
    StageCountOut,
)
from app.db.models import Deal, EventLog, Organization, PipelineStage
from app.organizations.service import (
    DEFAULT_ACTIVITY_WINDOW_DAYS,
    DEFAULT_STALE_DEAL_DAYS,
    resolve_analytics_settings,
)

STALE_DEAL_DAYS = DEFAULT_STALE_DEAL_DAYS
ACTIVITY_WINDOW_DAYS = DEFAULT_ACTIVITY_WINDOW_DAYS
REFRESH_STRATEGY = "query_time"
WON_STAGE_NAME = "Won"


def _days_since(now: datetime, moment: datetime) -> int:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)

    return max((now - moment).days, 0)


def _cycle_days(created_at: datetime, updated_at: datetime) -> int:
    start = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
    end = updated_at if updated_at.tzinfo else updated_at.replace(tzinfo=UTC)
    return max((end - start).days, 0)


def _as_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _sum_amounts(values: list[Decimal | float | int | None]) -> float | None:
    total = Decimal("0")
    has_value = False
    for value in values:
        if value is None:
            continue
        total += Decimal(str(value))
        has_value = True
    return round(float(total), 2) if has_value else None


def _dominant_currency(currencies: list[str], fallback: str = "RUB") -> str:
    cleaned = [item for item in currencies if item]
    if not cleaned:
        return fallback
    return Counter(cleaned).most_common(1)[0][0]


def get_analytics_summary(session: Session, organization_id: UUID) -> AnalyticsSummaryOut:
    organization = session.get(Organization, organization_id)
    analytics_settings = resolve_analytics_settings(
        organization.settings if organization is not None else None
    )
    stale_deal_days = analytics_settings.stale_deal_days
    activity_window_days = analytics_settings.activity_window_days

    now = datetime.now(UTC)
    activity_since = now - timedelta(days=activity_window_days)
    stale_before = now - timedelta(days=stale_deal_days)

    stage_rows = session.execute(
        select(
            PipelineStage.id,
            PipelineStage.name,
            func.count(Deal.id),
            func.sum(Deal.amount),
        )
        .join(Deal, Deal.stage_id == PipelineStage.id)
        .where(
            Deal.organization_id == organization_id,
            PipelineStage.organization_id == organization_id,
        )
        .group_by(PipelineStage.id, PipelineStage.name, PipelineStage.position)
        .order_by(PipelineStage.position.asc())
    ).all()

    deals_by_stage = [
        StageCountOut(
            stage_id=str(row[0]),
            stage_name=row[1],
            count=int(row[2] or 0),
            amount_total=_as_float(row[3]),
        )
        for row in stage_rows
    ]

    total_deals = sum(item.count for item in deals_by_stage)
    won_deals = next((item.count for item in deals_by_stage if item.stage_name == WON_STAGE_NAME), 0)

    all_deals = session.scalars(select(Deal).where(Deal.organization_id == organization_id)).all()
    stage_names = {
        row[0]: row[1]
        for row in session.execute(
            select(PipelineStage.id, PipelineStage.name).where(
                PipelineStage.organization_id == organization_id
            )
        ).all()
    }

    currency = _dominant_currency([deal.currency for deal in all_deals])
    open_deals_list = [deal for deal in all_deals if deal.status == "open"]
    open_deals = len(open_deals_list)
    open_pipeline_amount = _sum_amounts(
        [deal.amount for deal in open_deals_list if deal.currency == currency]
    )

    won_deals_list = [
        deal for deal in all_deals if stage_names.get(deal.stage_id) == WON_STAGE_NAME
    ]
    won_amount = _sum_amounts(
        [deal.amount for deal in won_deals_list if deal.currency == currency]
    )

    amounts_for_avg = [
        deal.amount
        for deal in all_deals
        if deal.amount is not None and deal.currency == currency
    ]
    avg_deal_amount = (
        round(sum(float(item) for item in amounts_for_avg) / len(amounts_for_avg), 2)
        if amounts_for_avg
        else None
    )

    win_rate = round(won_deals / total_deals * 100, 1) if total_deals > 0 else None

    close_days = [_cycle_days(deal.created_at, deal.updated_at) for deal in won_deals_list]
    avg_days_to_close = (
        round(sum(close_days) / len(close_days), 1) if close_days else None
    )

    total_events = int(
        session.scalar(
            select(func.count())
            .select_from(EventLog)
            .where(EventLog.organization_id == organization_id)
        )
        or 0
    )
    recent_events = int(
        session.scalar(
            select(func.count())
            .select_from(EventLog)
            .where(
                EventLog.organization_id == organization_id,
                EventLog.recorded_at >= activity_since,
            )
        )
        or 0
    )

    stale_deals = session.scalars(
        select(Deal)
        .where(
            Deal.organization_id == organization_id,
            Deal.status == "open",
            Deal.updated_at < stale_before,
        )
        .order_by(Deal.updated_at.asc())
        .limit(10)
    ).all()

    overdue_count = int(
        session.scalar(
            select(func.count())
            .select_from(Deal)
            .where(
                Deal.organization_id == organization_id,
                Deal.status == "open",
                Deal.updated_at < stale_before,
            )
        )
        or 0
    )

    return AnalyticsSummaryOut(
        computed_at=now,
        refresh_strategy=REFRESH_STRATEGY,
        deals_by_stage=deals_by_stage,
        conversion=ConversionOut(
            total_deals=total_deals,
            won_deals=won_deals,
            open_deals=open_deals,
            win_rate=win_rate,
            currency=currency,
            open_pipeline_amount=open_pipeline_amount,
            won_amount=won_amount,
            avg_deal_amount=avg_deal_amount,
        ),
        cycle=CycleOut(
            avg_days_to_close=avg_days_to_close,
            won_sample_size=len(won_deals_list),
        ),
        activity=ActivityOut(
            total_events=total_events,
            events_last_7_days=recent_events,
            activity_window_days=activity_window_days,
        ),
        follow_up=FollowUpOut(
            stale_threshold_days=stale_deal_days,
            overdue_count=overdue_count,
            deals=[
                FollowUpDealOut(
                    deal_id=str(deal.id),
                    title=deal.title,
                    days_since_update=_days_since(now, deal.updated_at),
                    amount=_as_float(deal.amount),
                    currency=deal.currency,
                    status=deal.status,
                    stage_name=stage_names.get(deal.stage_id, "Unknown"),
                )
                for deal in stale_deals
            ],
        ),
    )
