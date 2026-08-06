import type { EventLog } from "@/lib/api/crm";

type EventTimelineProps = {
  events: EventLog[];
};

const eventTypeLabels: Record<string, string> = {
  "company.created": "Компания создана",
  "company.updated": "Компания обновлена",
  "contact.created": "Контакт создан",
  "contact.updated": "Контакт обновлён",
  "deal.created": "Сделка создана",
  "deal.updated": "Сделка обновлена",
  "deal.stage_changed": "Этап сделки изменён",
  "communication.received": "Получено сообщение",
  "communication.sent": "Отправлено сообщение",
};

const stageLabels: Record<string, string> = {
  New: "Новая",
  Qualified: "Квалифицирована",
  Won: "Завершена",
};

const payloadKeyLabels: Record<string, string> = {
  full_name: "Имя",
  email: "Email",
  phone: "Телефон",
  company_id: "Компания",
  title: "Название",
  stage: "Этап",
  to_stage: "Новый этап",
  telegram_chat_id: "Telegram Chat ID",
};

function formatPayloadValue(key: string, value: unknown): string {
  if (key === "stage" || key === "to_stage") {
    const raw = String(value);
    return stageLabels[raw] ?? raw;
  }

  return String(value);
}

function formatPayload(event: EventLog): string | null {
  if (event.event_type === "communication.received" || event.event_type === "communication.sent") {
    const channel = event.payload.channel_type;
    const direction = event.payload.direction === "inbound" ? "входящее" : "исходящее";
    const preview = typeof event.payload.body_preview === "string" ? event.payload.body_preview : "";

    return [channel, direction, preview].filter(Boolean).join(" · ");
  }

  const entries = Object.entries(event.payload).filter(([key]) => key !== "seed");

  if (entries.length === 0) {
    return null;
  }

  return entries
    .map(([key, value]) => {
      const label = payloadKeyLabels[key] ?? key;
      return `${label}: ${formatPayloadValue(key, value)}`;
    })
    .join(", ");
}

export function EventTimeline({ events }: EventTimelineProps) {
  if (events.length === 0) {
    return <p className="text-sm text-shell-muted">Событий пока нет.</p>;
  }

  return (
    <ul className="space-y-3">
      {events.map((event) => {
        const payloadText = formatPayload(event);

        return (
          <li
            key={event.id}
            className="rounded-md border border-shell-border bg-shell-panel px-4 py-3 text-sm"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium text-white">
                {eventTypeLabels[event.event_type] ?? event.event_type}
              </span>
              <time className="text-xs text-shell-muted">
                {new Date(event.recorded_at).toLocaleString("ru-RU")}
              </time>
            </div>
            {payloadText ? <p className="mt-2 text-xs text-shell-muted">{payloadText}</p> : null}
          </li>
        );
      })}
    </ul>
  );
}
