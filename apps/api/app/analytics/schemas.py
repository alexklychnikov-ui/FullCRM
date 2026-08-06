from datetime import datetime

from pydantic import BaseModel, Field


class StageCountOut(BaseModel):
    stage_id: str
    stage_name: str
    count: int
    amount_total: float | None = None


class ConversionOut(BaseModel):
    total_deals: int
    won_deals: int
    open_deals: int
    win_rate: float | None = Field(
        default=None,
        description="Won deals as percentage of total deals",
    )
    currency: str = "RUB"
    open_pipeline_amount: float | None = None
    won_amount: float | None = None
    avg_deal_amount: float | None = None


class CycleOut(BaseModel):
    avg_days_to_close: float | None = None
    won_sample_size: int = 0


class ActivityOut(BaseModel):
    total_events: int
    events_last_7_days: int
    activity_window_days: int = 7


class FollowUpDealOut(BaseModel):
    deal_id: str
    title: str
    days_since_update: int
    amount: float | None = None
    currency: str = "RUB"
    status: str
    stage_name: str


class FollowUpOut(BaseModel):
    stale_threshold_days: int
    overdue_count: int
    deals: list[FollowUpDealOut]


class AnalyticsSummaryOut(BaseModel):
    computed_at: datetime
    refresh_strategy: str
    deals_by_stage: list[StageCountOut]
    conversion: ConversionOut
    cycle: CycleOut
    activity: ActivityOut
    follow_up: FollowUpOut
