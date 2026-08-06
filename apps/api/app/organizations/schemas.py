from pydantic import BaseModel, Field


class AnalyticsSettingsOut(BaseModel):
    stale_deal_days: int = Field(default=7, ge=1, le=365)
    activity_window_days: int = Field(default=7, ge=1, le=365)


class AnalyticsSettingsPatch(BaseModel):
    stale_deal_days: int | None = Field(default=None, ge=1, le=365)
    activity_window_days: int | None = Field(default=None, ge=1, le=365)


class OrganizationSettingsOut(BaseModel):
    analytics: AnalyticsSettingsOut


class OrganizationSettingsPatch(BaseModel):
    analytics: AnalyticsSettingsPatch | None = None
