"use client";

import type { Communication } from "@/lib/api/communications";
import { useI18n } from "@/lib/i18n";
import { resolveChannelName } from "@/lib/i18n/labels";

type CommunicationTimelineProps = {
  items: Communication[];
};

export function CommunicationTimeline({ items }: CommunicationTimelineProps) {
  const { t } = useI18n();

  if (items.length === 0) {
    return <p className="text-sm text-shell-muted">Сообщений пока нет.</p>;
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
              {resolveChannelName(item.channel_type, t)}
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
