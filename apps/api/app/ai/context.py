from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import (
    Communication,
    CommunicationThread,
    Company,
    Contact,
    Deal,
    EventLog,
    PipelineStage,
)

MAX_COMMUNICATIONS = 20
MAX_RELATED_DEALS = 15
MAX_EVENTS = 20
BODY_PREVIEW_LIMIT = 400

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s\-()]{7,}\d)")


@dataclass(frozen=True)
class CommunicationSnippet:
    channel: str
    direction: str
    occurred_at: str
    body_preview: str


@dataclass(frozen=True)
class RelatedDealSummary:
    title: str
    status: str
    stage_name: str
    amount: str | None
    currency: str
    days_open: int
    days_to_close: int | None
    is_won: bool
    updated_at: str


@dataclass(frozen=True)
class DealEventSnippet:
    event_type: str
    recorded_at: str
    summary: str


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
    days_open: int
    recent_event_count: int
    communications: tuple[CommunicationSnippet, ...]
    deal_events: tuple[DealEventSnippet, ...]
    related_deals: tuple[RelatedDealSummary, ...]


def _sanitize_text(value: str | None, limit: int = BODY_PREVIEW_LIMIT) -> str:
    if not value:
        return ""
    cleaned = _EMAIL_RE.sub("[email]", value)
    cleaned = _PHONE_RE.sub("[phone]", cleaned)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > limit:
        return f"{cleaned[:limit].rstrip()}…"
    return cleaned


def _days_between(start: datetime, end: datetime) -> int:
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    return max((end - start).days, 0)


def _is_won_stage(stage_name: str) -> bool:
    key = stage_name.strip().lower()
    return key in {"won", "завершена", "closed won"}


def _event_summary(event: EventLog) -> str:
    payload = event.payload if isinstance(event.payload, dict) else {}
    parts: list[str] = []

    for key in ("from_stage", "to_stage", "stage", "status", "direction", "channel_type"):
        value = payload.get(key)
        if value:
            parts.append(f"{key}={value}")

    preview = payload.get("body_preview")
    if isinstance(preview, str) and preview.strip():
        parts.append(f"preview={_sanitize_text(preview, 120)}")

    if not parts and payload:
        # Keep payload shallow and PII-safe: only scalar keys/values as short tags.
        for key, value in list(payload.items())[:4]:
            if isinstance(value, (str, int, float, bool)):
                text = _sanitize_text(str(value), 80) if isinstance(value, str) else str(value)
                parts.append(f"{key}={text}")

    return "; ".join(parts) if parts else "без деталей"


def _load_stage_names(session: Session, organization_id: UUID) -> dict[UUID, str]:
    rows = session.execute(
        select(PipelineStage.id, PipelineStage.name).where(
            PipelineStage.organization_id == organization_id
        )
    ).all()
    return {row[0]: row[1] for row in rows}


def _load_communications(
    session: Session,
    organization_id: UUID,
    *,
    deal_id: UUID,
    company_id: UUID | None,
    contact_id: UUID | None,
) -> tuple[CommunicationSnippet, ...]:
    entity_filters = [CommunicationThread.deal_id == deal_id]
    if company_id is not None:
        entity_filters.append(CommunicationThread.company_id == company_id)
    if contact_id is not None:
        entity_filters.append(CommunicationThread.contact_id == contact_id)

    threads = session.scalars(
        select(CommunicationThread).where(
            CommunicationThread.organization_id == organization_id,
            or_(*entity_filters),
        )
    ).all()
    if not threads:
        return ()

    thread_ids = [thread.id for thread in threads]
    communications = session.scalars(
        select(Communication)
        .where(
            Communication.organization_id == organization_id,
            Communication.thread_id.in_(thread_ids),
        )
        .order_by(Communication.occurred_at.desc())
        .limit(MAX_COMMUNICATIONS)
    ).all()

    return tuple(
        CommunicationSnippet(
            channel=item.channel_type,
            direction=item.direction,
            occurred_at=item.occurred_at.isoformat(),
            body_preview=_sanitize_text(item.body),
        )
        for item in communications
    )


def _load_deal_events(
    session: Session,
    organization_id: UUID,
    deal_id: UUID,
) -> tuple[DealEventSnippet, ...]:
    events = session.scalars(
        select(EventLog)
        .where(
            EventLog.organization_id == organization_id,
            EventLog.deal_id == deal_id,
        )
        .order_by(EventLog.recorded_at.desc())
        .limit(MAX_EVENTS)
    ).all()

    return tuple(
        DealEventSnippet(
            event_type=event.event_type,
            recorded_at=event.recorded_at.isoformat(),
            summary=_event_summary(event),
        )
        for event in events
    )


def _load_related_deals(
    session: Session,
    organization_id: UUID,
    *,
    current_deal_id: UUID,
    company_id: UUID | None,
    stage_names: dict[UUID, str],
    now: datetime,
) -> tuple[RelatedDealSummary, ...]:
    if company_id is None:
        return ()

    deals = session.scalars(
        select(Deal)
        .where(
            Deal.organization_id == organization_id,
            Deal.company_id == company_id,
            Deal.id != current_deal_id,
        )
        .order_by(Deal.updated_at.desc())
        .limit(MAX_RELATED_DEALS)
    ).all()

    related: list[RelatedDealSummary] = []
    for item in deals:
        stage_name = stage_names.get(item.stage_id, "Unknown")
        is_won = _is_won_stage(stage_name) or item.status.lower() in {"won", "closed"}
        end_point = item.updated_at if is_won or item.status.lower() != "open" else now
        days_open = _days_between(item.created_at, end_point)
        days_to_close = days_open if is_won else None
        related.append(
            RelatedDealSummary(
                title=item.title,
                status=item.status,
                stage_name=stage_name,
                amount=str(item.amount) if item.amount is not None else None,
                currency=item.currency,
                days_open=days_open,
                days_to_close=days_to_close,
                is_won=is_won,
                updated_at=item.updated_at.isoformat(),
            )
        )
    return tuple(related)


def build_deal_context(session: Session, organization_id: UUID, deal: Deal) -> DealAiContext:
    now = datetime.now(UTC)
    stage_names = _load_stage_names(session, organization_id)
    stage = stage_names.get(deal.stage_id, "Unknown")

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
        has_contact = (
            session.scalar(
                select(Contact.id).where(
                    Contact.id == deal.contact_id,
                    Contact.organization_id == organization_id,
                )
            )
            is not None
        )

    communications = _load_communications(
        session,
        organization_id,
        deal_id=deal.id,
        company_id=deal.company_id,
        contact_id=deal.contact_id,
    )
    deal_events = _load_deal_events(session, organization_id, deal.id)
    related_deals = _load_related_deals(
        session,
        organization_id,
        current_deal_id=deal.id,
        company_id=deal.company_id,
        stage_names=stage_names,
        now=now,
    )

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
        stage_name=stage,
        company_name=company_name,
        has_contact=has_contact,
        days_open=_days_between(deal.created_at, now),
        recent_event_count=int(recent_event_count or 0),
        communications=communications,
        deal_events=deal_events,
        related_deals=related_deals,
    )


def context_to_prompt_payload(context: DealAiContext) -> dict[str, Any]:
    won = [item for item in context.related_deals if item.is_won]
    avg_days_to_close: float | None = None
    if won:
        avg_days_to_close = round(
            sum(item.days_to_close or item.days_open for item in won) / len(won),
            1,
        )

    return {
        "response_language": "ru",
        "current_deal": {
            "title": context.title,
            "amount": context.amount,
            "currency": context.currency,
            "status": context.status,
            "stage": context.stage_name,
            "company": context.company_name,
            "has_contact": context.has_contact,
            "days_open": context.days_open,
            "recent_event_count": context.recent_event_count,
        },
        "communications": [
            {
                "channel": item.channel,
                "direction": item.direction,
                "occurred_at": item.occurred_at,
                "body_preview": item.body_preview,
            }
            for item in context.communications
        ],
        "deal_events": [
            {
                "event_type": item.event_type,
                "recorded_at": item.recorded_at,
                "summary": item.summary,
            }
            for item in context.deal_events
        ],
        "company_deal_history": {
            "related_count": len(context.related_deals),
            "won_count": len(won),
            "avg_days_to_close_won": avg_days_to_close,
            "deals": [
                {
                    "title": item.title,
                    "status": item.status,
                    "stage": item.stage_name,
                    "amount": item.amount,
                    "currency": item.currency,
                    "days_open": item.days_open,
                    "days_to_close": item.days_to_close,
                    "is_won": item.is_won,
                    "updated_at": item.updated_at,
                }
                for item in context.related_deals
            ],
        },
        "analysis_focus": [
            "качество и полнота коммуникации по текущей сделке",
            "темп и паттерны закрытия прошлых сделок этой компании",
            "риски затягивания относительно avg_days_to_close_won",
            "что устроило/не устроило клиента по сигналам из переписки и событий",
            "конкретный следующий шаг менеджера",
        ],
    }
