import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.config import Settings

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def telegram_live(settings: Settings) -> bool:
    return settings.telegram_enabled and bool(settings.telegram_bot_token)


def telegram_status(settings: Settings) -> tuple[str, str]:
    if telegram_live(settings):
        return "live", "Polling mode enabled via TELEGRAM_BOT_TOKEN and TELEGRAM_ENABLED"

    if settings.telegram_bot_token and not settings.telegram_enabled:
        return "disabled", "TELEGRAM_BOT_TOKEN is set but TELEGRAM_ENABLED is false"

    return "stub", "Set TELEGRAM_BOT_TOKEN and TELEGRAM_ENABLED=true to enable polling"


def fetch_telegram_updates(settings: Settings, offset: int | None = None) -> list[dict[str, Any]]:
    if not telegram_live(settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram integration is not enabled",
        )

    token = settings.telegram_bot_token
    assert token is not None

    params: dict[str, str | int] = {"timeout": 0, "limit": 50}

    if offset is not None:
        params["offset"] = offset

    query = "&".join(f"{key}={value}" for key, value in params.items())
    url = TELEGRAM_API_BASE.format(token=token, method=f"getUpdates?{query}")

    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram API error: {error.code}",
        ) from error
    except URLError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram API unreachable: {error.reason}",
        ) from error

    if not payload.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Telegram API returned an error",
        )

    return payload.get("result", [])


def extract_inbound_messages(updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    for update in updates:
        message = update.get("message") or update.get("edited_message")

        if not message:
            continue

        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = message.get("text")

        if chat_id is None or not text:
            continue

        messages.append(
            {
                "update_id": update.get("update_id"),
                "chat_id": str(chat_id),
                "message_id": str(message.get("message_id")),
                "text": text,
                "from_username": (message.get("from") or {}).get("username"),
            }
        )

    return messages
