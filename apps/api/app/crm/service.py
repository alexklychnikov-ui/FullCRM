from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.auth.service import AuthenticatedUser
from app.crm.events import write_event_log
from app.crm.schemas import (
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    ContactCreate,
    ContactOut,
    ContactUpdate,
    DealCreate,
    DealOut,
    DealUpdate,
    PipelineOut,
    PipelineStageOut,
)
from app.db.models import Company, Contact, Deal, Pipeline, PipelineStage, User


def _owner_from_meta(meta: dict[str, Any]) -> UUID | None:
    raw = meta.get("owner_user_id")

    if raw is None:
        return None

    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _set_owner_meta(meta: dict[str, Any], owner_user_id: UUID | None) -> dict[str, Any]:
    updated = dict(meta)

    if owner_user_id is None:
        updated.pop("owner_user_id", None)
    else:
        updated["owner_user_id"] = str(owner_user_id)

    return updated


def _telegram_from_meta(meta: dict[str, Any]) -> str | None:
    raw = meta.get("telegram_chat_id")

    if raw is None:
        return None

    value = str(raw).strip()
    return value or None


def _set_telegram_meta(meta: dict[str, Any], telegram_chat_id: str | None) -> dict[str, Any]:
    updated = dict(meta)

    if telegram_chat_id is None or not str(telegram_chat_id).strip():
        updated.pop("telegram_chat_id", None)
    else:
        updated["telegram_chat_id"] = str(telegram_chat_id).strip()

    return updated


def contact_to_out(contact: Contact) -> ContactOut:
    return ContactOut(
        id=contact.id,
        organization_id=contact.organization_id,
        company_id=contact.company_id,
        full_name=contact.full_name,
        email=contact.email,
        phone=contact.phone,
        telegram_chat_id=_telegram_from_meta(contact.meta),
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


def deal_to_out(deal: Deal) -> DealOut:
    return DealOut(
        id=deal.id,
        organization_id=deal.organization_id,
        pipeline_id=deal.pipeline_id,
        stage_id=deal.stage_id,
        company_id=deal.company_id,
        contact_id=deal.contact_id,
        title=deal.title,
        amount=deal.amount,
        currency=deal.currency,
        status=deal.status,
        owner_user_id=_owner_from_meta(deal.meta),
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


def get_company_or_404(session: Session, organization_id: UUID, company_id: UUID) -> Company:
    company = session.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.organization_id == organization_id,
        )
    )

    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    return company


def get_contact_or_404(session: Session, organization_id: UUID, contact_id: UUID) -> Contact:
    contact = session.scalar(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
        )
    )

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    return contact


def get_deal_or_404(session: Session, organization_id: UUID, deal_id: UUID) -> Deal:
    deal = session.scalar(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == organization_id,
        )
    )

    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return deal


def ensure_org_user(session: Session, organization_id: UUID, user_id: UUID) -> None:
    user = session.scalar(
        select(User.id).where(
            User.id == user_id,
            User.organization_id == organization_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid owner user")


def ensure_company_ref(session: Session, organization_id: UUID, company_id: UUID | None) -> None:
    if company_id is None:
        return

    get_company_or_404(session, organization_id, company_id)


def ensure_contact_ref(session: Session, organization_id: UUID, contact_id: UUID | None) -> None:
    if contact_id is None:
        return

    get_contact_or_404(session, organization_id, contact_id)


def get_pipeline_stage_or_404(
    session: Session,
    organization_id: UUID,
    pipeline_id: UUID,
    stage_id: UUID,
) -> PipelineStage:
    stage = session.scalar(
        select(PipelineStage).where(
            PipelineStage.id == stage_id,
            PipelineStage.pipeline_id == pipeline_id,
            PipelineStage.organization_id == organization_id,
        )
    )

    if stage is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pipeline stage")

    return stage


def list_companies(session: Session, organization_id: UUID) -> list[CompanyOut]:
    companies = session.scalars(
        select(Company)
        .where(Company.organization_id == organization_id)
        .order_by(Company.name.asc())
    ).all()

    return [CompanyOut.model_validate(company) for company in companies]


def create_company(
    session: Session,
    actor: AuthenticatedUser,
    payload: CompanyCreate,
) -> CompanyOut:
    company = Company(
        organization_id=actor.organization_id,
        name=payload.name.strip(),
        domain=payload.domain.strip() if payload.domain else None,
    )
    session.add(company)
    session.flush()

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="company.created",
        entity_type="company",
        entity_id=company.id,
        company_id=company.id,
        payload={"name": company.name},
    )
    session.commit()
    session.refresh(company)

    return CompanyOut.model_validate(company)


def update_company(
    session: Session,
    actor: AuthenticatedUser,
    company_id: UUID,
    payload: CompanyUpdate,
) -> CompanyOut:
    company = get_company_or_404(session, actor.organization_id, company_id)
    changes: dict[str, object] = {}

    if payload.name is not None:
        company.name = payload.name.strip()
        changes["name"] = company.name

    if payload.domain is not None:
        company.domain = payload.domain.strip() or None
        changes["domain"] = company.domain

    if not changes:
        return CompanyOut.model_validate(company)

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="company.updated",
        entity_type="company",
        entity_id=company.id,
        company_id=company.id,
        payload=changes,
    )
    session.commit()
    session.refresh(company)

    return CompanyOut.model_validate(company)


def list_contacts(session: Session, organization_id: UUID) -> list[ContactOut]:
    contacts = session.scalars(
        select(Contact)
        .where(Contact.organization_id == organization_id)
        .order_by(Contact.full_name.asc())
    ).all()

    return [contact_to_out(contact) for contact in contacts]


def create_contact(
    session: Session,
    actor: AuthenticatedUser,
    payload: ContactCreate,
) -> ContactOut:
    ensure_company_ref(session, actor.organization_id, payload.company_id)

    contact = Contact(
        organization_id=actor.organization_id,
        company_id=payload.company_id,
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower() if payload.email else None,
        phone=payload.phone.strip() if payload.phone else None,
        meta=_set_telegram_meta({}, payload.telegram_chat_id),
    )
    session.add(contact)
    session.flush()

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="contact.created",
        entity_type="contact",
        entity_id=contact.id,
        contact_id=contact.id,
        company_id=contact.company_id,
        payload={"full_name": contact.full_name},
    )
    session.commit()
    session.refresh(contact)

    return contact_to_out(contact)


def update_contact(
    session: Session,
    actor: AuthenticatedUser,
    contact_id: UUID,
    payload: ContactUpdate,
) -> ContactOut:
    contact = get_contact_or_404(session, actor.organization_id, contact_id)
    changes: dict[str, object] = {}

    if payload.full_name is not None:
        contact.full_name = payload.full_name.strip()
        changes["full_name"] = contact.full_name

    if payload.email is not None:
        contact.email = payload.email.strip().lower() or None
        changes["email"] = contact.email

    if payload.phone is not None:
        contact.phone = payload.phone.strip() or None
        changes["phone"] = contact.phone

    if payload.company_id is not None:
        ensure_company_ref(session, actor.organization_id, payload.company_id)
        contact.company_id = payload.company_id
        changes["company_id"] = str(payload.company_id)

    if "telegram_chat_id" in payload.model_fields_set:
        contact.meta = _set_telegram_meta(contact.meta, payload.telegram_chat_id)
        flag_modified(contact, "meta")
        changes["telegram_chat_id"] = _telegram_from_meta(contact.meta)

    if not changes:
        return contact_to_out(contact)

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="contact.updated",
        entity_type="contact",
        entity_id=contact.id,
        contact_id=contact.id,
        company_id=contact.company_id,
        payload=changes,
    )
    session.commit()
    session.refresh(contact)

    return contact_to_out(contact)


def list_deals(session: Session, organization_id: UUID) -> list[DealOut]:
    deals = session.scalars(
        select(Deal)
        .where(Deal.organization_id == organization_id)
        .order_by(Deal.updated_at.desc())
    ).all()

    return [deal_to_out(deal) for deal in deals]


def create_deal(
    session: Session,
    actor: AuthenticatedUser,
    payload: DealCreate,
) -> DealOut:
    get_pipeline_stage_or_404(session, actor.organization_id, payload.pipeline_id, payload.stage_id)
    ensure_company_ref(session, actor.organization_id, payload.company_id)
    ensure_contact_ref(session, actor.organization_id, payload.contact_id)

    owner_user_id = payload.owner_user_id or actor.id
    ensure_org_user(session, actor.organization_id, owner_user_id)

    deal = Deal(
        organization_id=actor.organization_id,
        pipeline_id=payload.pipeline_id,
        stage_id=payload.stage_id,
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        title=payload.title.strip(),
        amount=payload.amount,
        currency=payload.currency.upper(),
        status=payload.status,
        meta=_set_owner_meta({}, owner_user_id),
    )
    session.add(deal)
    session.flush()

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="deal.created",
        entity_type="deal",
        entity_id=deal.id,
        deal_id=deal.id,
        company_id=deal.company_id,
        contact_id=deal.contact_id,
        payload={"title": deal.title, "stage_id": str(deal.stage_id)},
    )
    session.commit()
    session.refresh(deal)

    return deal_to_out(deal)


def update_deal(
    session: Session,
    actor: AuthenticatedUser,
    deal_id: UUID,
    payload: DealUpdate,
) -> DealOut:
    deal = get_deal_or_404(session, actor.organization_id, deal_id)
    changes: dict[str, object] = {}

    if payload.title is not None:
        deal.title = payload.title.strip()
        changes["title"] = deal.title

    if payload.company_id is not None:
        ensure_company_ref(session, actor.organization_id, payload.company_id)
        deal.company_id = payload.company_id
        changes["company_id"] = str(payload.company_id)

    if payload.contact_id is not None:
        ensure_contact_ref(session, actor.organization_id, payload.contact_id)
        deal.contact_id = payload.contact_id
        changes["contact_id"] = str(payload.contact_id)

    if payload.amount is not None:
        deal.amount = payload.amount
        changes["amount"] = str(payload.amount)

    if payload.currency is not None:
        deal.currency = payload.currency.upper()
        changes["currency"] = deal.currency

    if payload.status is not None:
        deal.status = payload.status
        changes["status"] = deal.status

    if payload.owner_user_id is not None:
        ensure_org_user(session, actor.organization_id, payload.owner_user_id)
        deal.meta = _set_owner_meta(deal.meta, payload.owner_user_id)
        changes["owner_user_id"] = str(payload.owner_user_id)

    if not changes:
        return deal_to_out(deal)

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="deal.updated",
        entity_type="deal",
        entity_id=deal.id,
        deal_id=deal.id,
        company_id=deal.company_id,
        contact_id=deal.contact_id,
        payload=changes,
    )
    session.commit()
    session.refresh(deal)

    return deal_to_out(deal)


def transition_deal_stage(
    session: Session,
    actor: AuthenticatedUser,
    deal_id: UUID,
    stage_id: UUID,
) -> DealOut:
    deal = get_deal_or_404(session, actor.organization_id, deal_id)

    if deal.stage_id == stage_id:
        return deal_to_out(deal)

    get_pipeline_stage_or_404(session, actor.organization_id, deal.pipeline_id, stage_id)
    previous_stage_id = deal.stage_id
    deal.stage_id = stage_id

    write_event_log(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type="deal.stage_changed",
        entity_type="deal",
        entity_id=deal.id,
        deal_id=deal.id,
        company_id=deal.company_id,
        contact_id=deal.contact_id,
        payload={
            "from_stage_id": str(previous_stage_id),
            "to_stage_id": str(stage_id),
        },
    )
    session.commit()
    session.refresh(deal)

    return deal_to_out(deal)


def list_pipelines(session: Session, organization_id: UUID) -> list[PipelineOut]:
    pipelines = session.scalars(
        select(Pipeline)
        .where(Pipeline.organization_id == organization_id)
        .order_by(Pipeline.is_default.desc(), Pipeline.name.asc())
    ).all()

    result: list[PipelineOut] = []

    for pipeline in pipelines:
        stages = session.scalars(
            select(PipelineStage)
            .where(
                PipelineStage.pipeline_id == pipeline.id,
                PipelineStage.organization_id == organization_id,
            )
            .order_by(PipelineStage.position.asc())
        ).all()
        result.append(
            PipelineOut(
                id=pipeline.id,
                organization_id=pipeline.organization_id,
                name=pipeline.name,
                is_default=pipeline.is_default,
                stages=[PipelineStageOut.model_validate(stage) for stage in stages],
            )
        )

    return result


def list_assignees(session: Session, organization_id: UUID) -> list[dict[str, str]]:
    users = session.scalars(
        select(User)
        .where(User.organization_id == organization_id, User.is_active.is_(True))
        .order_by(User.full_name.asc())
    ).all()

    return [{"id": str(user.id), "full_name": user.full_name, "email": user.email} for user in users]


def list_event_logs(
    session: Session,
    organization_id: UUID,
    *,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> list[dict[str, object]]:
    from app.db.models import EventLog

    query = select(EventLog).where(EventLog.organization_id == organization_id)

    if entity_type:
        query = query.where(EventLog.entity_type == entity_type)

    if entity_id:
        query = query.where(EventLog.entity_id == entity_id)

    events = session.scalars(query.order_by(EventLog.recorded_at.desc()).limit(50)).all()

    return [
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": str(event.entity_id) if event.entity_id else None,
            "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None,
            "payload": event.payload,
            "recorded_at": event.recorded_at.isoformat(),
        }
        for event in events
    ]
