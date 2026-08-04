from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics import service
from app.analytics.schemas import AnalyticsSummaryOut
from app.auth.dependencies import require_module, require_permission
from app.auth.service import AuthenticatedUser
from app.db.session import get_db_session

router = APIRouter(prefix="/analytics", tags=["analytics"])

analytics_module = require_module("analytics")
analytics_read = require_permission("analytics.read")


@router.get("/summary", response_model=AnalyticsSummaryOut)
def get_analytics_summary(
    user: AuthenticatedUser = Depends(analytics_module),
    _: AuthenticatedUser = Depends(analytics_read),
    session: Session = Depends(get_db_session),
) -> AnalyticsSummaryOut:
    return service.get_analytics_summary(session, user.organization_id)
