from app.ai.context import DealAiContext
from app.ai.schemas import AiDraftOut, AiInsightOut, AiNextActionOut, AiScoreOut

STAGE_SCORES: dict[str, tuple[int, str]] = {
    "new": (25, "Ранний этап"),
    "qualified": (55, "Квалифицированная возможность"),
    "won": (95, "Сделка завершена"),
}

STAGE_NAMES_RU: dict[str, str] = {
    "new": "Новая",
    "qualified": "Квалифицирована",
    "won": "Завершена",
}


def _stage_key(stage_name: str) -> str:
    return stage_name.strip().lower()


def _stage_label_ru(stage_name: str) -> str:
    return STAGE_NAMES_RU.get(_stage_key(stage_name), stage_name)


def generate_mock_insights(context: DealAiContext) -> AiInsightOut:
    stage_key = _stage_key(context.stage_name)
    stage_ru = _stage_label_ru(context.stage_name)
    probability, label = STAGE_SCORES.get(stage_key, (40, "В работе"))

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
        "new": ("Назначить квалификационный созвон", "high"),
        "qualified": ("Отправить follow-up по коммерческому предложению", "medium"),
        "won": ("Запросить отзыв или обсудить допродажу", "low"),
    }
    action, priority = next_actions.get(
        stage_key,
        ("Проверить активность по сделке и обновить этап", "medium"),
    )

    company_ref = context.company_name or "клиента"
    contact_ref = "контактное лицо" if context.has_contact else "заинтересованное лицо"

    draft_body = (
        f"Здравствуйте!\n\n"
        f"Возвращаюсь к сделке «{context.title}» для {company_ref}. "
        f"Текущий этап: {stage_ru}. "
        "Готов ответить на вопросы и согласовать следующие шаги.\n\n"
        "С уважением"
    )

    return AiInsightOut(
        deal_id=context.deal_id,
        provider_mode="mock",
        advisory=True,
        score=AiScoreOut(
            probability=probability,
            label=label,
            rationale=(
                f"Справочная оценка по этапу «{stage_ru}» "
                f"и {context.recent_event_count} недавним событиям в CRM."
            ),
        ),
        next_action=AiNextActionOut(action=action, priority=priority),  # type: ignore[arg-type]
        draft_suggestion=AiDraftOut(
            subject=f"Follow-up по сделке: {context.title}",
            body=draft_body,
            channel_hint="email",
        ),
    )
