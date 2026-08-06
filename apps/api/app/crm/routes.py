from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import current_user, require_module, require_permission
from app.auth.service import AuthenticatedUser
from app.crm import service
from app.crm.schemas import (
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    ContactCreate,
    ContactOut,
    ContactUpdate,
    DealCreate,
    DealOut,
    DealTransition,
    DealUpdate,
    PipelineOut,
)
from app.db.session import get_db_session

router = APIRouter(prefix="/crm", tags=["crm"])

crm_module = require_module("crm")
crm_read = require_permission("crm.read")
crm_write = require_permission("crm.write")


@router.get("/companies", response_model=list[CompanyOut])
def get_companies(
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> list[CompanyOut]:
    return service.list_companies(session, user.organization_id)


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def post_company(
    payload: CompanyCreate,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> CompanyOut:
    return service.create_company(session, user, payload)


@router.get("/companies/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: UUID,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> CompanyOut:
    company = service.get_company_or_404(session, user.organization_id, company_id)
    return CompanyOut.model_validate(company)


@router.patch("/companies/{company_id}", response_model=CompanyOut)
def patch_company(
    company_id: UUID,
    payload: CompanyUpdate,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> CompanyOut:
    return service.update_company(session, user, company_id, payload)


@router.get("/contacts", response_model=list[ContactOut])
def get_contacts(
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> list[ContactOut]:
    return service.list_contacts(session, user.organization_id)


@router.post("/contacts", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def post_contact(
    payload: ContactCreate,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> ContactOut:
    return service.create_contact(session, user, payload)


@router.get("/contacts/{contact_id}", response_model=ContactOut)
def get_contact(
    contact_id: UUID,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> ContactOut:
    contact = service.get_contact_or_404(session, user.organization_id, contact_id)
    return service.contact_to_out(contact)


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
def patch_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> ContactOut:
    return service.update_contact(session, user, contact_id, payload)


@router.get("/deals", response_model=list[DealOut])
def get_deals(
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> list[DealOut]:
    return service.list_deals(session, user.organization_id)


@router.post("/deals", response_model=DealOut, status_code=status.HTTP_201_CREATED)
def post_deal(
    payload: DealCreate,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> DealOut:
    return service.create_deal(session, user, payload)


@router.get("/deals/{deal_id}", response_model=DealOut)
def get_deal(
    deal_id: UUID,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> DealOut:
    deal = service.get_deal_or_404(session, user.organization_id, deal_id)
    return service.deal_to_out(deal)


@router.patch("/deals/{deal_id}", response_model=DealOut)
def patch_deal(
    deal_id: UUID,
    payload: DealUpdate,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> DealOut:
    return service.update_deal(session, user, deal_id, payload)


@router.post("/deals/{deal_id}/transition", response_model=DealOut)
def post_deal_transition(
    deal_id: UUID,
    payload: DealTransition,
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_write),
    session: Session = Depends(get_db_session),
) -> DealOut:
    return service.transition_deal_stage(session, user, deal_id, payload.stage_id)


@router.get("/pipelines", response_model=list[PipelineOut])
def get_pipelines(
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> list[PipelineOut]:
    return service.list_pipelines(session, user.organization_id)


@router.get("/assignees")
def get_assignees(
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> list[dict[str, str]]:
    return service.list_assignees(session, user.organization_id)


@router.get("/event-logs")
def get_event_logs(
    entity_type: str | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    user: AuthenticatedUser = Depends(crm_module),
    _: AuthenticatedUser = Depends(crm_read),
    session: Session = Depends(get_db_session),
) -> list[dict[str, object]]:
    return service.list_event_logs(
        session,
        user.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
