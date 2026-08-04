import logging
from uuid import UUID

logger = logging.getLogger("fullcrm.ai")

AI_USE_CASES = ("score", "next_action", "draft_suggestion")


def log_ai_call(
    *,
    organization_id: UUID,
    deal_id: UUID,
    provider: str,
    mode: str,
    latency_ms: int,
    degraded: bool = False,
    error_type: str | None = None,
) -> None:
    logger.info(
        "ai.call org_id=%s deal_id=%s provider=%s mode=%s use_cases=%s latency_ms=%d degraded=%s error_type=%s",
        organization_id,
        deal_id,
        provider,
        mode,
        ",".join(AI_USE_CASES),
        latency_ms,
        degraded,
        error_type or "-",
    )
