"use client";

import { useState } from "react";

import type { AiInsight, AiStatus } from "@/lib/api/ai";
import { fetchDealAiInsights } from "@/lib/api/ai";

type DealAiAdvisoryPanelProps = {
  dealId: string;
  initialStatus: AiStatus | null;
};

const modeStyles: Record<string, string> = {
  mock: "text-amber-400",
  live: "text-emerald-400",
  degraded: "text-orange-400",
};

const priorityStyles: Record<string, string> = {
  high: "text-red-400",
  medium: "text-amber-400",
  low: "text-shell-muted",
};

export function DealAiAdvisoryPanel({ dealId, initialStatus }: DealAiAdvisoryPanelProps) {
  const [status] = useState(initialStatus);
  const [insight, setInsight] = useState<AiInsight | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function loadInsights() {
    setPending(true);
    setError("");

    try {
      const result = await fetchDealAiInsights(dealId);
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
        <h2 className="text-lg font-medium">ИИ-рекомендации</h2>
        {status ? (
          <span className={`text-xs uppercase ${modeStyles[status.mode] ?? "text-shell-muted"}`}>
            {status.mode}
          </span>
        ) : null}
      </div>
      <p className="mb-4 text-xs text-shell-muted">
        Справочные рекомендации ИИ, не источник истины. Проверяйте данные CRM перед действиями.
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
              <span className="font-medium">Вероятность</span>
              <span className={modeStyles[insight.provider_mode] ?? "text-shell-muted"}>
                {insight.provider_mode}
              </span>
            </div>
            <p className="text-2xl font-semibold text-white">{insight.score.probability}%</p>
            <p className="text-shell-muted">{insight.score.label}</p>
            <p className="mt-2 text-xs text-shell-muted">{insight.score.rationale}</p>
          </div>
          <div className="rounded border border-shell-border p-3">
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="font-medium">Следующее действие</span>
              <span className={priorityStyles[insight.next_action.priority] ?? "text-shell-muted"}>
                {insight.next_action.priority}
              </span>
            </div>
            <p>{insight.next_action.action}</p>
          </div>
          <div className="rounded border border-shell-border p-3">
            <span className="mb-1 block font-medium">Черновик ({insight.draft_suggestion.channel_hint})</span>
            {insight.draft_suggestion.subject ? (
              <p className="mb-2 text-xs text-shell-muted">Тема: {insight.draft_suggestion.subject}</p>
            ) : null}
            <pre className="whitespace-pre-wrap text-xs text-shell-muted">{insight.draft_suggestion.body}</pre>
          </div>
        </div>
      ) : null}
    </section>
  );
}
