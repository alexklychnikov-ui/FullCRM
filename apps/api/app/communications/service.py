from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.service import AuthenticatedUser
from app.communications.events import write_communication_event
from app.communications.schemas import CommunicationOut, IntegrationsStatusOut, IntegrationStatus, MessageCreate
from app.communications.poll_cooldown import assert_poll_allowed
from app.communications.telegram import extract_inbound_messages, fetch_telegram_updates, telegram_live, telegram_status
from app.config import Settings
from app.crm.service import ensure_company_ref, ensure_contact_ref, get_deal_or_404
from app.db.models import Communication, CommunicationThread, Contact

MANUAL_BLOCKED_CHANNELS = frozenset({"gmail", "calendar", "telegram"})


def integrations_status(settings: Settings) -> IntegrationsStatusOut:
    telegram_mode, telegram_reason = telegram_status(settings)

    return IntegrationsStatusOut(
        integrations=[
            IntegrationStatus(
                channel="telegram",
                mode=telegram_mode,
                reason=telegram_reason,
            ),
            IntegrationStatus(
                channel="gmail",
                mode="stub",
                reason="OAuth/token policy not configured for MVP; use manual email channel entries",
            ),
            IntegrationStatus(
                channel="calendar",
                mode="stub",
                reason="OAuth/token policy not configured for MVP; calendar sync deferred",
            ),
        ]
    )


def _communication_to_out(thread: CommunicationThread, communication: Communication) -> CommunicationOut:
    return CommunicationOut(
        id=communication.id,
        organization_id=communication.organization_id,
        thread_id=communication.thread_id,
        direction=communication.direction,
        channel_type=communication.channel_type,
        body=communication.body,
        external_message_id=communication.external_message_id,
        contact_id=thread.contact_id,
        company_id=thread.company_id,
        deal_id=thread.deal_id,
        occurred_at=communication.occurred_at,
    )


def _find_contact_by_telegram_chat(
    session: Session,
    organization_id: UUID,
    chat_id: str,
) -> Contact | None:
    contacts = session.scalars(
        select(Contact).where(Contact.organization_id == organization_id)
    ).all()

    for contact in contacts:
        raw = contact.meta.get("telegram_chat_id")

        if raw is not None and str(raw) == chat_id:
            return contact

    return None


def _resolve_thread_refs(
    session: Session,
    organization_id: UUID,
    *,
    contact_id: UUID | None,
    company_id: UUID | None,
    deal_id: UUID | None,
) -> tuple[UUID | None, UUID | None, UUID | None]:
    resolved_contact_id = contact_id
    resolved_company_id = company_id
    resolved_deal_id = deal_id

    if deal_id is not None:
        deal = get_deal_or_404(session, organization_id, deal_id)
        resolved_deal_id = deal.id
        resolved_contact_id = resolved_contact_id or deal.contact_id
        resolved_company_id = resolved_company_id or deal.company_id

    if contact_id is not None:
        ensure_contact_ref(session, organization_id, contact_id)
        resolved_contact_id = contact_id

    if company_id is not None:
        ensure_company_ref(session, organization_id, company_id)
        resolved_company_id = company_id

    return resolved_contact_id, resolved_company_id, resolved_deal_id


def get_or_create_thread(
    session: Session,
    organization_id: UUID,
    *,
    channel_type: str,
    external_thread_id: str,
    contact_id: UUID | None = None,
    company_id: UUID | None = None,
    deal_id: UUID | None = None,
    subject: str | None = None,
) -> CommunicationThread:
    thread = session.scalar(
        select(CommunicationThread).where(
            CommunicationThread.organization_id == organization_id,
            CommunicationThread.channel_type == channel_type,
            CommunicationThread.external_thread_id == external_thread_id,
        )
    )

    if thread is not None:
        changed = False

        if contact_id and thread.contact_id is None:
            thread.contact_id = contact_id
            changed = True

        if company_id and thread.company_id is None:
            thread.company_id = company_id
            changed = True

        if deal_id and thread.deal_id is None:
            thread.deal_id = deal_id
            changed = True

        if changed:
            session.flush()

        return thread

    thread = CommunicationThread(
        organization_id=organization_id,
        channel_type=channel_type,
        external_thread_id=external_thread_id,
        contact_id=contact_id,
        company_id=company_id,
        deal_id=deal_id,
        subject=subject,
    )
    session.add(thread)
    session.flush()
    return thread


def list_timeline(
    session: Session,
    organization_id: UUID,
    *,
    contact_id: UUID | None = None,
    company_id: UUID | None = None,
    deal_id: UUID | None = None,
    limit: int = 50,
) -> list[CommunicationOut]:
    if not any([contact_id, company_id, deal_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of contact_id, company_id, or deal_id is required",
        )

    thread_filters = [CommunicationThread.organization_id == organization_id]
    entity_filters = []

    if contact_id is not None:
        entity_filters.append(CommunicationThread.contact_id == contact_id)

    if company_id is not None:
        entity_filters.append(CommunicationThread.company_id == company_id)

    if deal_id is not None:
        entity_filters.append(CommunicationThread.deal_id == deal_id)

    thread_filters.append(or_(*entity_filters))

    threads = session.scalars(select(CommunicationThread).where(*thread_filters)).all()
    thread_ids = [thread.id for thread in threads]

    if not thread_ids:
        return []

    thread_by_id = {thread.id: thread for thread in threads}

    communications = session.scalars(
        select(Communication)
        .where(
            Communication.organization_id == organization_id,
            Communication.thread_id.in_(thread_ids),
        )
        .order_by(Communication.occurred_at.desc())
        .limit(limit)
    ).all()

    return [_communication_to_out(thread_by_id[item.thread_id], item) for item in communications]


def create_message(
    session: Session,
    actor: AuthenticatedUser,
    payload: MessageCreate,
) -> CommunicationOut:
    if payload.channel_type in MANUAL_BLOCKED_CHANNELS:
        if payload.channel_type == "telegram":
            detail = "telegram messages must be ingested via POST /communications/telegram/poll only"
        else:
            detail = f"{payload.channel_type} is a stub integration in MVP; use channel_type=email"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    contact_id, company_id, deal_id = _resolve_thread_refs(
        session,
        actor.organization_id,
        contact_id=payload.contact_id,
        company_id=payload.company_id,
        deal_id=payload.deal_id,
    )

    external_thread_id = payload.external_thread_id

    if external_thread_id is None:
        if contact_id is not None:
            external_thread_id = f"{payload.channel_type}:contact:{contact_id}"
        else:
            external_thread_id = f"{payload.channel_type}:manual:{uuid4()}"

    thread = get_or_create_thread(
        session,
        actor.organization_id,
        channel_type=payload.channel_type,
        external_thread_id=external_thread_id,
        contact_id=contact_id,
        company_id=company_id,
        deal_id=deal_id,
    )

    external_message_id = payload.external_message_id or f"manual:{uuid4()}"

    existing = session.scalar(
        select(Communication).where(
            Communication.thread_id == thread.id,
            Communication.external_message_id == external_message_id,
        )
    )

    if existing is not None:
        return _communication_to_out(thread, existing)

    communication = Communication(
        organization_id=actor.organization_id,
        thread_id=thread.id,
        direction=payload.direction,
        channel_type=payload.channel_type,
        external_message_id=external_message_id,
        body=payload.body,
        payload={"source": "manual"},
        occurred_at=datetime.now(tz=UTC),
    )
    session.add(communication)
    session.flush()

    event_type = "communication.received" if payload.direction == "inbound" else "communication.sent"

    write_communication_event(
        session,
        organization_id=actor.organization_id,
        actor=actor,
        event_type=event_type,
        communication_id=communication.id,
        contact_id=thread.contact_id,
        company_id=thread.company_id,
        deal_id=thread.deal_id,
        payload={
            "channel_type": payload.channel_type,
            "direction": payload.direction,
            "body_preview": payload.body[:200],
        },
    )
    session.commit()
    session.refresh(communication)

    return _communication_to_out(thread, communication)


def _ingest_telegram_message(
    session: Session,
    organization_id: UUID,
    *,
    chat_id: str,
    message_id: str,
    text: str,
    from_username: str | None,
) -> str:
    contact = _find_contact_by_telegram_chat(session, organization_id, chat_id)

    if contact is None:
        return "skipped_unmatched"

    thread = get_or_create_thread(
        session,
        organization_id,
        channel_type="telegram",
        external_thread_id=chat_id,
        contact_id=contact.id,
        company_id=contact.company_id,
        subject=f"Telegram chat {chat_id}",
    )

    existing = session.scalar(
        select(Communication).where(
            Communication.thread_id == thread.id,
            Communication.external_message_id == message_id,
        )
    )

    if existing is not None:
        return "duplicate"

    communication = Communication(
        organization_id=organization_id,
        thread_id=thread.id,
        direction="inbound",
        channel_type="telegram",
        external_message_id=message_id,
        body=text,
        payload={"from_username": from_username, "source": "telegram_poll"},
        occurred_at=datetime.now(tz=UTC),
    )
    session.add(communication)
    session.flush()

    write_communication_event(
        session,
        organization_id=organization_id,
        actor=None,
        event_type="communication.received",
        communication_id=communication.id,
        contact_id=thread.contact_id,
        company_id=thread.company_id,
        deal_id=thread.deal_id,
        payload={
            "channel_type": "telegram",
            "direction": "inbound",
            "body_preview": text[:200],
            "telegram_chat_id": chat_id,
        },
    )
    return "created"


def poll_telegram(
    session: Session,
    settings: Settings,
    organization_id: UUID,
) -> dict[str, Any]:
    if not telegram_live(settings):
        mode, reason = telegram_status(settings)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Telegram polling unavailable ({mode}): {reason}",
        )

    assert_poll_allowed(organization_id, settings.telegram_poll_cooldown_seconds)

    updates = fetch_telegram_updates(settings)
    messages = extract_inbound_messages(updates)
    created = 0
    skipped_unmatched = 0

    for message in messages:
        result = _ingest_telegram_message(
            session,
            organization_id,
            chat_id=message["chat_id"],
            message_id=message["message_id"],
            text=message["text"],
            from_username=message.get("from_username"),
        )

        if result == "created":
            created += 1
        elif result == "skipped_unmatched":
            skipped_unmatched += 1

    session.commit()

    return {
        "processed": len(messages),
        "created": created,
        "skipped_unmatched": skipped_unmatched,
        "mode": "live",
    }
