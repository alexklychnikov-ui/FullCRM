"use client";

import { useState } from "react";

import type { AiStatus, OrgAiInsight } from "@/lib/api/ai";
import { fetchAnalyticsAiInsights } from "@/lib/api/ai";
import { useI18n } from "@/lib/i18n";
import { resolveAiMode, resolveAiPriority } from "@/lib/i18n/labels";

type AnalyticsAiAdvisoryPanelProps = {
  initialStatus: AiStatus | null;
};

const modeStyles: Record<string, string> = {
  mock: "text-amber-400",
  live: "text-emerald-400",
  degraded: "text-orange-400",
  disabled: "text-shell-muted",
};

const priorityStyles: Record<string, string> = {
  high: "text-red-400",
  medium: "text-amber-400",
  low: "text-shell-muted",
};

export function AnalyticsAiAdvisoryPanel({ initialStatus }: AnalyticsAiAdvisoryPanelProps) {
  const { t } = useI18n();
  const [status] = useState(initialStatus);
  const [insight, setInsight] = useState<OrgAiInsight | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function loadInsights() {
    setPending(true);
    setError("");

    try {
      const result = await fetchAnalyticsAiInsights();
      setInsight(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось получить рекомендации");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="rounded-md border border-shell-border bg-shell-panel p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium">ИИ-рекомендации по бизнесу</h2>
        {status ? (
          <span className={`text-xs uppercase ${modeStyles[status.mode] ?? "text-shell-muted"}`}>
            {resolveAiMode(status.mode, t)}
          </span>
        ) : null}
      </div>
      <p className="mb-4 text-xs text-shell-muted">
        Сводная оценка pipeline, перспектив и план развития. Справочно — проверяйте цифры CRM.
        {status ? ` ${status.reason}` : ""}
      </p>
      <button
        className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        disabled={pending}
        onClick={loadInsights}
        type="button"
      >
        {pending ? "Запрос..." : "Получить рекомендации"}
      </button>
      {error ? <p className="mt-3 text-sm text-red-400">{error}</p> : null}
      {insight ? (
        <div className="mt-4 space-y-4 text-sm">
          <div className="rounded border border-shell-border p-3">
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="font-medium">Здоровье коммерции</span>
              <span className={modeStyles[insight.provider_mode] ?? "text-shell-muted"}>
                {resolveAiMode(insight.provider_mode, t)}
              </span>
            </div>
            <p className="text-2xl font-semibold text-white">{insight.health.probability}%</p>
            <p className="text-shell-muted">{insight.health.label}</p>
            <p className="mt-2 text-xs text-shell-muted">{insight.health.rationale}</p>
          </div>

          <div className="rounded border border-shell-border p-3">
            <span className="mb-1 block font-medium">Перспективы</span>
            <p className="text-shell-muted">{insight.outlook}</p>
          </div>

          <div className="rounded border border-shell-border p-3">
            <span className="mb-2 block font-medium">Рекомендации</span>
            <ul className="space-y-3">
              {insight.recommendations.map((item) => (
                <li key={`${item.title}-${item.priority}`}>
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-medium text-white">{item.title}</span>
                    <span className={priorityStyles[item.priority] ?? "text-shell-muted"}>
                      {resolveAiPriority(item.priority, t)}
                    </span>
                  </div>
                  <p className="text-xs text-shell-muted">{item.detail}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded border border-shell-border p-3">
            <span className="mb-1 block font-medium">План развития</span>
            <pre className="whitespace-pre-wrap text-xs text-shell-muted">{insight.planning}</pre>
          </div>
        </div>
      ) : null}
    </section>
  );
}
