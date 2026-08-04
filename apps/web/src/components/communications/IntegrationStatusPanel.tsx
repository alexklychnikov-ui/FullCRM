import type { IntegrationStatus } from "@/lib/api/communications";

type IntegrationStatusPanelProps = {
  integrations: IntegrationStatus[];
};

const modeStyles: Record<string, string> = {
  live: "text-emerald-400",
  disabled: "text-amber-400",
  stub: "text-shell-muted",
};

export function IntegrationStatusPanel({ integrations }: IntegrationStatusPanelProps) {
  return (
    <ul className="grid gap-3 md:grid-cols-3">
      {integrations.map((item) => (
        <li
          key={item.channel}
          className="rounded-md border border-shell-border bg-shell-panel px-4 py-3 text-sm"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium capitalize text-white">{item.channel}</span>
            <span className={modeStyles[item.mode] ?? "text-shell-muted"}>{item.mode}</span>
          </div>
          <p className="mt-2 text-xs text-shell-muted">{item.reason}</p>
        </li>
      ))}
    </ul>
  );
}
