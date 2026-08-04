from datetime import datetime

from pydantic import BaseModel, Field


class StageCountOut(BaseModel):
    stage_id: str
    stage_name: str
    count: int


class ConversionOut(BaseModel):
    total_deals: int
    won_deals: int
    open_deals: int
    win_rate: float | None = Field(
        default=None,
        description="Won deals as percentage of total deals",
    )


class ActivityOut(BaseModel):
    total_events: int
    events_last_7_days: int


class FollowUpDealOut(BaseModel):
    deal_id: str
    title: str
    days_since_update: int


class FollowUpOut(BaseModel):
    stale_threshold_days: int
    overdue_count: int
    deals: list[FollowUpDealOut]


class AnalyticsSummaryOut(BaseModel):
    computed_at: datetime
    refresh_strategy: str
    deals_by_stage: list[StageCountOut]
    conversion: ConversionOut
    activity: ActivityOut
    follow_up: FollowUpOut
