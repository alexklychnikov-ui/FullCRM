from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AiScoreOut(BaseModel):
    probability: int = Field(ge=0, le=100)
    label: str
    rationale: str


class AiNextActionOut(BaseModel):
    action: str
    priority: Literal["low", "medium", "high"]


class AiDraftOut(BaseModel):
    subject: str | None = None
    body: str
    channel_hint: str


class AiInsightOut(BaseModel):
    deal_id: UUID
    provider_mode: Literal["mock", "live", "degraded"]
    advisory: bool = True
    score: AiScoreOut
    next_action: AiNextActionOut
    draft_suggestion: AiDraftOut


class OrgAiRecommendationOut(BaseModel):
    title: str
    detail: str
    priority: Literal["low", "medium", "high"]


class OrgAiInsightOut(BaseModel):
    provider_mode: Literal["mock", "live", "degraded"]
    advisory: bool = True
    health: AiScoreOut
    outlook: str
    recommendations: list[OrgAiRecommendationOut] = Field(default_factory=list)
    planning: str


class AiStatusOut(BaseModel):
    mode: Literal["mock", "live", "disabled"]
    reason: str
    use_cases: list[str]
