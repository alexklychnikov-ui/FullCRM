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

    if context.recent_event_count == 0 and len(context.communications) == 0:
        probability = max(probability - 15, 5)
    elif len(context.communications) == 0:
        probability = max(probability - 8, 5)

    if context.amount:
        try:
            amount_value = float(context.amount)
            if amount_value >= 10000:
                probability = min(probability + 5, 99)
        except ValueError:
            pass

    won = [item for item in context.related_deals if item.is_won]
    if won:
        avg_close = sum(item.days_to_close or item.days_open for item in won) / len(won)
        if context.days_open > avg_close * 1.3:
            probability = max(probability - 10, 5)
            label = "Риск затягивания"
        elif context.days_open <= avg_close:
            probability = min(probability + 5, 99)

    inbound = sum(1 for item in context.communications if item.direction == "inbound")
    if inbound >= 2:
        probability = min(probability + 5, 99)

    next_actions: dict[str, tuple[str, str]] = {
        "new": ("Назначить квалификационный созвон и зафиксировать критерии успеха", "high"),
        "qualified": ("Отправить follow-up по КП со ссылкой на договорённости из переписки", "medium"),
        "won": ("Запросить отзыв и обсудить допродажу на базе успешного цикла", "low"),
    }
    action, priority = next_actions.get(
        stage_key,
        ("Проверить активность по сделке и обновить этап", "medium"),
    )
    if len(context.communications) == 0:
        action = "Инициировать контакт и зафиксировать канал коммуникации по сделке"
        priority = "high"
    elif context.days_open >= 14 and stage_key != "won":
        action = "Сделать контрольный созвон: сверить ожидания и снять блокеры закрытия"
        priority = "high"

    company_ref = context.company_name or "клиента"
    history_note = ""
    if won:
        avg_close = round(sum(item.days_to_close or item.days_open for item in won) / len(won))
        history_note = (
            f" Ранее по компании закрыто сделок: {len(won)}, "
            f"средний цикл ~{avg_close} дн."
        )
    elif context.related_deals:
        history_note = f" По компании есть {len(context.related_deals)} прошлых сделок без явного won."

    draft_body = (
        f"Здравствуйте!\n\n"
        f"Возвращаюсь к сделке «{context.title}» для {company_ref}. "
        f"Сделка открыта {context.days_open} дн., текущий этап: {_stage_label_ru(context.stage_name)}. "
        "Предлагаю коротко сверить статус и согласовать следующий шаг.\n\n"
        "С уважением"
    )

    rationale = (
        f"Справочная BA-оценка: этап «{stage_ru}», открыта {context.days_open} дн., "
        f"сообщений {len(context.communications)}, событий CRM {context.recent_event_count}."
        f"{history_note}"
    )

    return AiInsightOut(
        deal_id=context.deal_id,
        provider_mode="mock",
        advisory=True,
        score=AiScoreOut(
            probability=probability,
            label=label,
            rationale=rationale,
        ),
        next_action=AiNextActionOut(action=action, priority=priority),  # type: ignore[arg-type]
        draft_suggestion=AiDraftOut(
            subject=f"Follow-up по сделке: {context.title}",
            body=draft_body,
            channel_hint="email",
        ),
    )
