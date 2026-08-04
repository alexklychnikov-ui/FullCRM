from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommunicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    thread_id: UUID
    direction: str
    channel_type: str
    body: str | None
    external_message_id: str | None
    contact_id: UUID | None
    company_id: UUID | None
    deal_id: UUID | None
    occurred_at: datetime


class MessageCreate(BaseModel):
    channel_type: str = Field(min_length=1, max_length=80)
    direction: str = Field(default="outbound", pattern="^(inbound|outbound)$")
    body: str = Field(min_length=1)
    contact_id: UUID | None = None
    company_id: UUID | None = None
    deal_id: UUID | None = None
    external_thread_id: str | None = Field(default=None, max_length=255)
    external_message_id: str | None = Field(default=None, max_length=255)


class IntegrationStatus(BaseModel):
    channel: str
    mode: str
    reason: str


class IntegrationsStatusOut(BaseModel):
    integrations: list[IntegrationStatus]


class TelegramPollOut(BaseModel):
    processed: int
    created: int
    skipped_unmatched: int
    mode: str
