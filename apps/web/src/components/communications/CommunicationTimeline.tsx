import type { Communication } from "@/lib/api/communications";

type CommunicationTimelineProps = {
  items: Communication[];
};

const channelLabels: Record<string, string> = {
  email: "Email",
  telegram: "Telegram",
  gmail: "Gmail (stub)",
  calendar: "Calendar (stub)",
};

export function CommunicationTimeline({ items }: CommunicationTimelineProps) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-shell-muted">Сообщений пока нет.</p>
    );
  }

  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li
          key={item.id}
          className="rounded-md border border-shell-border bg-shell-panel px-4 py-3 text-sm"
        >
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium text-white">
              {channelLabels[item.channel_type] ?? item.channel_type}
              {" · "}
              {item.direction === "inbound" ? "входящее" : "исходящее"}
            </span>
            <time className="text-xs text-shell-muted">
              {new Date(item.occurred_at).toLocaleString("ru-RU")}
            </time>
          </div>
          {item.body ? (
            <p className="mt-2 whitespace-pre-wrap text-shell-muted">{item.body}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
