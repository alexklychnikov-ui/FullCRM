import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.ai.context import DealAiContext, context_to_prompt_payload
from app.ai.schemas import AiDraftOut, AiInsightOut, AiNextActionOut, AiScoreOut
from app.config import Settings

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_AI_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are a CRM sales assistant for a Russian-speaking team. "
    "Return ONLY valid JSON with keys: "
    "score {probability 0-100, label, rationale}, "
    "next_action {action, priority low|medium|high}, "
    "draft_suggestion {subject, body, channel_hint}. "
    "All human-readable text values (label, rationale, action, subject, body) MUST be in Russian. "
    "Keep JSON keys in English. "
    "Use only the sanitized deal context provided. Do not invent PII."
)


class OpenAiProviderError(RuntimeError):
    pass


def generate_openai_insights(settings: Settings, context: DealAiContext) -> AiInsightOut:
    api_key = settings.openai_api_key

    if not api_key:
        raise OpenAiProviderError("OPENAI_API_KEY is not configured")

    payload = {
        "model": settings.ai_model or DEFAULT_AI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(context_to_prompt_payload(context), ensure_ascii=False),
            },
        ],
    }

    request = Request(
        OPENAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise OpenAiProviderError(f"OpenAI HTTP {error.code}") from error
    except URLError as error:
        raise OpenAiProviderError(f"OpenAI unreachable: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise OpenAiProviderError("OpenAI returned invalid JSON envelope") from error

    try:
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise OpenAiProviderError("OpenAI response missing expected fields") from error

    return _parse_insights(context.deal_id, parsed)


def _parse_insights(deal_id: Any, parsed: dict[str, Any]) -> AiInsightOut:
    score_raw = parsed.get("score") or {}
    next_raw = parsed.get("next_action") or {}
    draft_raw = parsed.get("draft_suggestion") or {}

    probability = int(score_raw.get("probability", 50))
    probability = max(0, min(100, probability))

    priority = str(next_raw.get("priority", "medium")).lower()
    if priority not in {"low", "medium", "high"}:
        priority = "medium"

    return AiInsightOut(
        deal_id=deal_id,
        provider_mode="live",
        advisory=True,
        score=AiScoreOut(
            probability=probability,
            label=str(score_raw.get("label") or "Оценка ИИ"),
            rationale=str(score_raw.get("rationale") or "Сформировано на основе контекста сделки."),
        ),
        next_action=AiNextActionOut(
            action=str(next_raw.get("action") or "Проверить сделку и спланировать следующий шаг"),
            priority=priority,  # type: ignore[arg-type]
        ),
        draft_suggestion=AiDraftOut(
            subject=draft_raw.get("subject"),
            body=str(draft_raw.get("body") or "Черновик недоступен."),
            channel_hint=str(draft_raw.get("channel_hint") or "email"),
        ),
    )
