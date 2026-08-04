import type { EventLog } from "@/lib/api/crm";

type EventTimelineProps = {
  events: EventLog[];
};

export function EventTimeline({ events }: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-shell-muted">Событий пока нет.</p>
    );
  }

  return (
    <ul className="space-y-3">
      {events.map((event) => (
        <li
          key={event.id}
          className="rounded-md border border-shell-border bg-shell-panel px-4 py-3 text-sm"
        >
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium text-white">{event.event_type}</span>
            <time className="text-xs text-shell-muted">
              {new Date(event.recorded_at).toLocaleString("ru-RU")}
            </time>
          </div>
          {Object.keys(event.payload).length > 0 ? (
            <pre className="mt-2 overflow-x-auto text-xs text-shell-muted">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
