from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import service
from app.ai.schemas import AiInsightOut, AiStatusOut, OrgAiInsightOut
from app.auth.dependencies import get_settings, require_module, require_permission
from app.auth.service import AuthenticatedUser
from app.config import Settings
from app.db.session import get_db_session

router = APIRouter(prefix="/ai", tags=["ai"])

ai_module = require_module("ai")
analytics_module = require_module("analytics")
ai_read = require_permission("ai.read")


@router.get("/status", response_model=AiStatusOut)
def get_ai_status(
    _: AuthenticatedUser = Depends(ai_module),
    __: AuthenticatedUser = Depends(ai_read),
    settings: Settings = Depends(get_settings),
) -> AiStatusOut:
    return service.ai_status(settings)


@router.get("/analytics/insights", response_model=OrgAiInsightOut)
def get_analytics_insights(
    user: AuthenticatedUser = Depends(ai_module),
    _: AuthenticatedUser = Depends(analytics_module),
    __: AuthenticatedUser = Depends(ai_read),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> OrgAiInsightOut:
    return service.get_org_analytics_insights(session, settings, user.organization_id)


@router.get("/deals/{deal_id}/insights", response_model=AiInsightOut)
def get_deal_insights(
    deal_id: UUID,
    user: AuthenticatedUser = Depends(ai_module),
    _: AuthenticatedUser = Depends(ai_read),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AiInsightOut:
    return service.get_deal_insights(session, settings, user.organization_id, deal_id)
