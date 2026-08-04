from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str | None = Field(default=None, max_length=255)


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    domain: str | None = Field(default=None, max_length=255)


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    domain: str | None
    created_at: datetime
    updated_at: datetime


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=80)
    company_id: UUID | None = None


class ContactUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=80)
    company_id: UUID | None = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    company_id: UUID | None
    full_name: str
    email: str | None
    phone: str | None
    created_at: datetime
    updated_at: datetime


class PipelineStageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pipeline_id: UUID
    name: str
    position: int
    probability: int


class PipelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    is_default: bool
    stages: list[PipelineStageOut]


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    pipeline_id: UUID
    stage_id: UUID
    company_id: UUID | None = None
    contact_id: UUID | None = None
    amount: Decimal | None = None
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    status: str = Field(default="open", max_length=40)
    owner_user_id: UUID | None = None


class DealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    company_id: UUID | None = None
    contact_id: UUID | None = None
    amount: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: str | None = Field(default=None, max_length=40)
    owner_user_id: UUID | None = None


class DealTransition(BaseModel):
    stage_id: UUID


class DealOut(BaseModel):
    id: UUID
    organization_id: UUID
    pipeline_id: UUID
    stage_id: UUID
    company_id: UUID | None
    contact_id: UUID | None
    title: str
    amount: Decimal | None
    currency: str
    status: str
    owner_user_id: UUID | None
    created_at: datetime
    updated_at: datetime


class AssigneeOut(BaseModel):
    id: UUID
    full_name: str
    email: str


class EventLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    entity_type: str
    entity_id: UUID | None
    actor_user_id: UUID | None
    payload: dict[str, object]
    recorded_at: datetime
