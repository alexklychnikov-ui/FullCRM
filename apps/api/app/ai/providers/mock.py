from app.ai.context import DealAiContext
from app.ai.schemas import AiDraftOut, AiInsightOut, AiNextActionOut, AiScoreOut

STAGE_SCORES: dict[str, tuple[int, str]] = {
    "new": (25, "Early stage"),
    "qualified": (55, "Qualified opportunity"),
    "won": (95, "Closed won"),
}


def _stage_key(stage_name: str) -> str:
    return stage_name.strip().lower()


def generate_mock_insights(context: DealAiContext) -> AiInsightOut:
    stage_key = _stage_key(context.stage_name)
    probability, label = STAGE_SCORES.get(stage_key, (40, "In progress"))

    if context.recent_event_count == 0:
        probability = max(probability - 10, 5)

    if context.amount:
        try:
            amount_value = float(context.amount)
            if amount_value >= 10000:
                probability = min(probability + 5, 99)
        except ValueError:
            pass

    next_actions: dict[str, tuple[str, str]] = {
        "new": ("Schedule qualification call", "high"),
        "qualified": ("Send proposal follow-up", "medium"),
        "won": ("Request testimonial or upsell review", "low"),
    }
    action, priority = next_actions.get(stage_key, ("Review deal activity and update stage", "medium"))

    company_ref = context.company_name or "the account"
    contact_ref = "your contact" if context.has_contact else "a stakeholder"

    draft_body = (
        f"Hi {contact_ref},\n\n"
        f"Following up on \"{context.title}\" for {company_ref}. "
        f"Current stage: {context.stage_name}. "
        "Happy to answer questions or align on next steps.\n\n"
        "Best regards"
    )

    return AiInsightOut(
        deal_id=context.deal_id,
        provider_mode="mock",
        advisory=True,
        score=AiScoreOut(
            probability=probability,
            label=label,
            rationale=f"Mock advisory based on stage '{context.stage_name}' and {context.recent_event_count} recent events.",
        ),
        next_action=AiNextActionOut(action=action, priority=priority),  # type: ignore[arg-type]
        draft_suggestion=AiDraftOut(
            subject=f"Follow-up: {context.title}",
            body=draft_body,
            channel_hint="email",
        ),
    )
