from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.service import AuthenticatedUser
from app.db.models import EventLog


def write_communication_event(
    session: Session,
    *,
    organization_id: UUID,
    actor: AuthenticatedUser | None,
    event_type: str,
    communication_id: UUID,
    contact_id: UUID | None = None,
    company_id: UUID | None = None,
    deal_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> EventLog:
    event = EventLog(
        organization_id=organization_id,
        actor_user_id=actor.id if actor else None,
        company_id=company_id,
        contact_id=contact_id,
        deal_id=deal_id,
        event_type=event_type,
        entity_type="communication",
        entity_id=communication_id,
        payload=payload or {},
    )
    session.add(event)
    session.flush()
    return event
