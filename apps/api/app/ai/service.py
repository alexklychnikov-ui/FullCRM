import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.context import build_deal_context
from app.ai.logging import log_ai_call
from app.ai.providers.mock import generate_mock_insights
from app.ai.providers.openai import OpenAiProviderError, generate_openai_insights
from app.ai.schemas import AiInsightOut, AiStatusOut
from app.config import Settings
from app.crm.service import get_deal_or_404

AI_USE_CASES = ["score", "next_action", "draft_suggestion"]


def ai_status(settings: Settings) -> AiStatusOut:
    if settings.ai_mock:
        return AiStatusOut(
            mode="mock",
            reason="AI_MOCK=true; deterministic mock advisory responses",
            use_cases=AI_USE_CASES,
        )

    if settings.openai_api_key:
        return AiStatusOut(
            mode="live",
            reason="OpenAI provider enabled via OPENAI_API_KEY",
            use_cases=AI_USE_CASES,
        )

    return AiStatusOut(
        mode="mock",
        reason="No OPENAI_API_KEY configured; falling back to mock advisory",
        use_cases=AI_USE_CASES,
    )


def _should_use_live(settings: Settings) -> bool:
    return not settings.ai_mock and bool(settings.openai_api_key)


def get_deal_insights(
    session: Session,
    settings: Settings,
    organization_id: UUID,
    deal_id: UUID,
) -> AiInsightOut:
    deal = get_deal_or_404(session, organization_id, deal_id)
    context = build_deal_context(session, organization_id, deal)
    started = time.perf_counter()

    if _should_use_live(settings):
        try:
            insights = generate_openai_insights(settings, context)
            latency_ms = int((time.perf_counter() - started) * 1000)
            log_ai_call(
                organization_id=organization_id,
                deal_id=deal_id,
                provider="openai",
                mode="live",
                latency_ms=latency_ms,
            )
            return insights
        except OpenAiProviderError as error:
            latency_ms = int((time.perf_counter() - started) * 1000)
            log_ai_call(
                organization_id=organization_id,
                deal_id=deal_id,
                provider="openai",
                mode="degraded",
                latency_ms=latency_ms,
                degraded=True,
                error_type=type(error).__name__,
            )
            degraded = generate_mock_insights(context)
            return degraded.model_copy(update={"provider_mode": "degraded"})

    insights = generate_mock_insights(context)
    latency_ms = int((time.perf_counter() - started) * 1000)
    log_ai_call(
        organization_id=organization_id,
        deal_id=deal_id,
        provider="mock",
        mode="mock",
        latency_ms=latency_ms,
    )
    return insights
