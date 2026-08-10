from datetime import datetime
from uuid import UUID

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


class OrganizationModuleOut(BaseModel):
    module_key: str
    enabled: bool


class OrganizationModulesOut(BaseModel):
    modules: list[OrganizationModuleOut]


class OrganizationModulePatchItem(BaseModel):
    module_key: str = Field(min_length=1, max_length=120)
    enabled: bool


class OrganizationModulesPatch(BaseModel):
    modules: list[OrganizationModulePatchItem] = Field(min_length=1)


class OrganizationRoleOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None


class OrganizationRolesOut(BaseModel):
    roles: list[OrganizationRoleOut]


class OrganizationUserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[str]
    created_at: datetime


class OrganizationUsersOut(BaseModel):
    users: list[OrganizationUserOut]


class OrganizationUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    roles: list[str] = Field(min_length=1)


class OrganizationUserPatch(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class OrganizationUserRolesPut(BaseModel):
    roles: list[str] = Field(min_length=1)
