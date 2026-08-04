from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Company, Contact, Deal, EventLog, PipelineStage


@dataclass(frozen=True)
class DealAiContext:
    deal_id: UUID
    title: str
    amount: str | None
    currency: str
    status: str
    stage_name: str
    company_name: str | None
    has_contact: bool
    recent_event_count: int


def build_deal_context(session: Session, organization_id: UUID, deal: Deal) -> DealAiContext:
    stage = session.scalar(
        select(PipelineStage.name).where(
            PipelineStage.id == deal.stage_id,
            PipelineStage.organization_id == organization_id,
        )
    )
    company_name: str | None = None

    if deal.company_id is not None:
        company_name = session.scalar(
            select(Company.name).where(
                Company.id == deal.company_id,
                Company.organization_id == organization_id,
            )
        )

    has_contact = False

    if deal.contact_id is not None:
        has_contact = session.scalar(
            select(Contact.id).where(
                Contact.id == deal.contact_id,
                Contact.organization_id == organization_id,
            )
        ) is not None

    recent_event_count = session.scalar(
        select(func.count())
        .select_from(EventLog)
        .where(
            EventLog.organization_id == organization_id,
            EventLog.deal_id == deal.id,
        )
    )

    return DealAiContext(
        deal_id=deal.id,
        title=deal.title,
        amount=str(deal.amount) if deal.amount is not None else None,
        currency=deal.currency,
        status=deal.status,
        stage_name=stage or "Unknown",
        company_name=company_name,
        has_contact=has_contact,
        recent_event_count=int(recent_event_count or 0),
    )


def context_to_prompt_payload(context: DealAiContext) -> dict[str, object]:
    return {
        "deal_title": context.title,
        "amount": context.amount,
        "currency": context.currency,
        "status": context.status,
        "stage": context.stage_name,
        "company": context.company_name,
        "has_contact": context.has_contact,
        "recent_events": context.recent_event_count,
    }
