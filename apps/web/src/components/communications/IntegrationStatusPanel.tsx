"use client";

import type { IntegrationStatus } from "@/lib/api/communications";
import { useI18n } from "@/lib/i18n";
import {
  resolveChannelName,
  resolveIntegrationMode,
  resolveIntegrationReason,
} from "@/lib/i18n/labels";

type IntegrationStatusPanelProps = {
  integrations: IntegrationStatus[];
};

const modeStyles: Record<string, string> = {
  live: "text-emerald-400",
  disabled: "text-amber-400",
  stub: "text-shell-muted",
};

export function IntegrationStatusPanel({ integrations }: IntegrationStatusPanelProps) {
  const { t } = useI18n();

  return (
    <ul className="grid gap-3 md:grid-cols-3">
      {integrations.map((item) => (
        <li
          key={item.channel}
          className="rounded-md border border-shell-border bg-shell-panel px-4 py-3 text-sm"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium text-white">{resolveChannelName(item.channel, t)}</span>
            <span className={modeStyles[item.mode] ?? "text-shell-muted"}>
              {resolveIntegrationMode(item.mode, t)}
            </span>
          </div>
          <p className="mt-2 text-xs text-shell-muted">
            {resolveIntegrationReason(item.reason, t)}
          </p>
        </li>
      ))}
    </ul>
  );
}
