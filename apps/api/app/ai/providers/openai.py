import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.ai.context import DealAiContext, context_to_prompt_payload
from app.ai.org_context import OrgAnalyticsAiContext, org_context_to_prompt_payload
from app.ai.schemas import (
    AiDraftOut,
    AiInsightOut,
    AiNextActionOut,
    AiScoreOut,
    OrgAiInsightOut,
    OrgAiRecommendationOut,
)
from app.config import Settings

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_AI_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "Ты — сильный бизнес-аналитик и sales operations advisor в B2B CRM. "
    "Твоя задача: дать управленческую рекомендацию по текущей сделке на основе фактов. "
    "Роль: анализируешь pipeline, коммуникации, циклы прошлых сделок компании и риски затягивания. "
    "Работай как senior BA: конкретные выводы, без воды, без общих лозунгов. "
    "Обязательно учитывай: "
    "1) всю переписку/сообщения по текущей сделке (канал, направление, содержание); "
    "2) события CRM по сделке; "
    "3) историю предыдущих сделок этой компании — сколько дней открыта/закрыта, won/не won, "
    "суммы, этапы, возможные сигналы удовлетворённости или проблем; "
    "4) сравнение текущего days_open с avg_days_to_close_won. "
    "Если данных мало — явно скажи об этом в rationale и предложи, какие факты нужно собрать. "
    "Не выдумывай факты, PII и детали, которых нет в контексте. "
    "Не используй реальные email/телефоны — в контексте они уже обезличены. "
    "Return ONLY valid JSON with keys: "
    "score {probability 0-100, label, rationale}, "
    "next_action {action, priority low|medium|high}, "
    "draft_suggestion {subject, body, channel_hint}. "
    "rationale должен ссылаться на конкретные сигналы из communications/deal_events/company_deal_history. "
    "action — один чёткий следующий шаг менеджера. "
    "draft_suggestion — готовый черновик сообщения клиенту, согласованный с анализом. "
    "All human-readable text values (label, rationale, action, subject, body) MUST be in Russian. "
    "Keep JSON keys in English."
)

ORG_SYSTEM_PROMPT = (
    "Ты — сильный бизнес-аналитик и руководитель sales operations в B2B CRM. "
    "Твоя задача: оценить ОБЩЕЕ состояние коммерции организации и дать план развития бизнеса. "
    "Работай как senior BA / commercial director advisor: конкретика, цифры из контекста, без воды. "
    "Обязательно анализируй: "
    "1) воронку и конверсию; "
    "2) денежный потенциал открытого pipeline и сумму завершённых; "
    "3) средний цикл закрытия и риски затягивания; "
    "4) просроченные сделки и активность; "
    "5) перспективы на ближайшие 2–4 недели; "
    "6) управленческие приоритеты развития бизнеса. "
    "Не выдумывай факты вне контекста. Не используй PII. "
    "Return ONLY valid JSON with keys: "
    "health {probability 0-100, label, rationale}, "
    "outlook (string), "
    "recommendations (array of {title, detail, priority low|medium|high}, 3 to 5 items), "
    "planning (string — план на 1-2 недели и на месяц). "
    "health.rationale и все тексты MUST be in Russian. Keep JSON keys in English."
)


class OpenAiProviderError(RuntimeError):
    pass


def _chat_json(settings: Settings, *, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
    api_key = settings.openai_api_key

    if not api_key:
        raise OpenAiProviderError("OPENAI_API_KEY is not configured")

    payload = {
        "model": settings.ai_model or DEFAULT_AI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
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
        with urlopen(request, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise OpenAiProviderError(f"OpenAI HTTP {error.code}") from error
    except URLError as error:
        raise OpenAiProviderError(f"OpenAI unreachable: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise OpenAiProviderError("OpenAI returned invalid JSON envelope") from error

    try:
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise OpenAiProviderError("OpenAI response missing expected fields") from error


def generate_openai_insights(settings: Settings, context: DealAiContext) -> AiInsightOut:
    parsed = _chat_json(
        settings,
        system_prompt=SYSTEM_PROMPT,
        user_payload=context_to_prompt_payload(context),
    )
    return _parse_insights(context.deal_id, parsed)


def generate_openai_org_insights(
    settings: Settings,
    context: OrgAnalyticsAiContext,
) -> OrgAiInsightOut:
    parsed = _chat_json(
        settings,
        system_prompt=ORG_SYSTEM_PROMPT,
        user_payload=org_context_to_prompt_payload(context),
    )
    return _parse_org_insights(parsed)


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


def _parse_org_insights(parsed: dict[str, Any]) -> OrgAiInsightOut:
    health_raw = parsed.get("health") or parsed.get("score") or {}
    probability = int(health_raw.get("probability", 50))
    probability = max(0, min(100, probability))

    recommendations_raw = parsed.get("recommendations") or []
    recommendations: list[OrgAiRecommendationOut] = []
    if isinstance(recommendations_raw, list):
        for item in recommendations_raw[:5]:
            if not isinstance(item, dict):
                continue
            priority = str(item.get("priority", "medium")).lower()
            if priority not in {"low", "medium", "high"}:
                priority = "medium"
            title = str(item.get("title") or "").strip()
            detail = str(item.get("detail") or "").strip()
            if not title or not detail:
                continue
            recommendations.append(
                OrgAiRecommendationOut(
                    title=title,
                    detail=detail,
                    priority=priority,  # type: ignore[arg-type]
                )
            )

    if not recommendations:
        recommendations.append(
            OrgAiRecommendationOut(
                title="Проверить воронку и просрочки",
                detail="Сверьте открытый pipeline и сделки без активности, затем назначьте next-step.",
                priority="medium",
            )
        )

    return OrgAiInsightOut(
        provider_mode="live",
        advisory=True,
        health=AiScoreOut(
            probability=probability,
            label=str(health_raw.get("label") or "Оценка здоровья pipeline"),
            rationale=str(
                health_raw.get("rationale") or "Сформировано на основе сводной аналитики организации."
            ),
        ),
        outlook=str(parsed.get("outlook") or "Перспективы требуют дополнительного анализа данных CRM."),
        recommendations=recommendations,
        planning=str(
            parsed.get("planning")
            or "Сформируйте недельный план по просрочкам и месячный фокус по конверсии."
        ),
    )
