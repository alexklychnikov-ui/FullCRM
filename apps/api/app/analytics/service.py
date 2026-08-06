from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    ActivityOut,
    AnalyticsSummaryOut,
    ConversionOut,
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
        StageCountOut(stage_id=str(row[0]), stage_name=row[1], count=int(row[2]))
        for row in stage_rows
    ]

    total_deals = sum(item.count for item in deals_by_stage)
    won_deals = next((item.count for item in deals_by_stage if item.stage_name == WON_STAGE_NAME), 0)
    open_deals = int(
        session.scalar(
            select(func.count())
            .select_from(Deal)
            .where(
                Deal.organization_id == organization_id,
                Deal.status == "open",
            )
        )
        or 0
    )

    win_rate = round(won_deals / total_deals * 100, 1) if total_deals > 0 else None

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
        ),
        activity=ActivityOut(
            total_events=total_events,
            events_last_7_days=recent_events,
        ),
        follow_up=FollowUpOut(
            stale_threshold_days=stale_deal_days,
            overdue_count=overdue_count,
            deals=[
                FollowUpDealOut(
                    deal_id=str(deal.id),
                    title=deal.title,
                    days_since_update=_days_since(now, deal.updated_at),
                )
                for deal in stale_deals
            ],
        ),
    )
