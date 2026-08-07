import logging
from uuid import UUID

logger = logging.getLogger("fullcrm.ai")

AI_USE_CASES = ("score", "next_action", "draft_suggestion")
ORG_AI_USE_CASES = ("health", "outlook", "recommendations", "planning")


def log_ai_call(
    *,
    organization_id: UUID,
    provider: str,
    mode: str,
    latency_ms: int,
    deal_id: UUID | None = None,
    use_cases: tuple[str, ...] = AI_USE_CASES,
    degraded: bool = False,
    error_type: str | None = None,
) -> None:
    logger.info(
        "ai.call org_id=%s deal_id=%s provider=%s mode=%s use_cases=%s latency_ms=%d degraded=%s error_type=%s",
        organization_id,
        deal_id or "-",
        provider,
        mode,
        ",".join(use_cases),
        latency_ms,
        degraded,
        error_type or "-",
    )
