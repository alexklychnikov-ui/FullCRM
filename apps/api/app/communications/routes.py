from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_settings, require_module, require_permission
from app.auth.service import AuthenticatedUser
from app.communications import service
from app.communications.schemas import (
    CommunicationOut,
    IntegrationsStatusOut,
    MessageCreate,
    TelegramPollOut,
)
from app.config import Settings
from app.db.session import get_db_session

router = APIRouter(prefix="/communications", tags=["communications"])

communications_module = require_module("communications")
communications_read = require_permission("communications.read")
communications_write = require_permission("communications.write")


@router.get("/integrations/status", response_model=IntegrationsStatusOut)
def get_integrations_status(
    _: AuthenticatedUser = Depends(communications_module),
    __: AuthenticatedUser = Depends(communications_read),
    settings: Settings = Depends(get_settings),
) -> IntegrationsStatusOut:
    return service.integrations_status(settings)


@router.get("/timeline", response_model=list[CommunicationOut])
def get_timeline(
    contact_id: UUID | None = Query(default=None),
    company_id: UUID | None = Query(default=None),
    deal_id: UUID | None = Query(default=None),
    user: AuthenticatedUser = Depends(communications_module),
    _: AuthenticatedUser = Depends(communications_read),
    session: Session = Depends(get_db_session),
) -> list[CommunicationOut]:
    return service.list_timeline(
        session,
        user.organization_id,
        contact_id=contact_id,
        company_id=company_id,
        deal_id=deal_id,
    )


@router.post("/messages", response_model=CommunicationOut, status_code=status.HTTP_201_CREATED)
def post_message(
    payload: MessageCreate,
    user: AuthenticatedUser = Depends(communications_module),
    _: AuthenticatedUser = Depends(communications_write),
    session: Session = Depends(get_db_session),
) -> CommunicationOut:
    return service.create_message(session, user, payload)


@router.post("/telegram/poll", response_model=TelegramPollOut)
def post_telegram_poll(
    user: AuthenticatedUser = Depends(communications_module),
    _: AuthenticatedUser = Depends(communications_write),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TelegramPollOut:
    result = service.poll_telegram(session, settings, user.organization_id)
    return TelegramPollOut(**result)
