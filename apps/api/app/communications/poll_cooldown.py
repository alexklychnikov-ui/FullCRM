from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import UUID

from fastapi import HTTPException, status

_lock = Lock()
_last_poll_at: dict[UUID, datetime] = {}


def assert_poll_allowed(organization_id: UUID, cooldown_seconds: int) -> None:
    if cooldown_seconds <= 0:
        return

    now = datetime.now(tz=UTC)

    with _lock:
        last_poll = _last_poll_at.get(organization_id)

        if last_poll is not None:
            elapsed = now - last_poll

            if elapsed < timedelta(seconds=cooldown_seconds):
                retry_after = cooldown_seconds - int(elapsed.total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Telegram poll cooldown active; retry in {retry_after}s",
                )

        _last_poll_at[organization_id] = now


def reset_poll_cooldowns() -> None:
    with _lock:
        _last_poll_at.clear()
