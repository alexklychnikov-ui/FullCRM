import type { AnalyticsSummary } from "@/lib/api/analytics";

type AnalyticsSummaryCardsProps = {
  summary: AnalyticsSummary;
};

function formatPercent(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

export function AnalyticsSummaryCards({ summary }: AnalyticsSummaryCardsProps) {
  const computedAt = new Date(summary.computed_at).toLocaleString("ru-RU");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium text-white">Аналитика CRM</h2>
        <p className="text-xs text-shell-muted">
          Обновлено: {computedAt} · {summary.refresh_strategy}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Сделки</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.conversion.total_deals}</p>
          <p className="mt-1 text-sm text-shell-muted">
            Открытых: {summary.conversion.open_deals} · Won: {summary.conversion.won_deals}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Конверсия в Won</p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {formatPercent(summary.conversion.win_rate)}
          </p>
          <p className="mt-1 text-sm text-shell-muted">Доля сделок на этапе Won</p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Активность</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.activity.total_events}</p>
          <p className="mt-1 text-sm text-shell-muted">
            За 7 дней: {summary.activity.events_last_7_days}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Просрочен follow-up</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.follow_up.overdue_count}</p>
          <p className="mt-1 text-sm text-shell-muted">
            Без обновления &gt; {summary.follow_up.stale_threshold_days} дн.
          </p>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Сделки по этапам</p>
          <ul className="mt-3 space-y-2">
            {summary.deals_by_stage.length > 0 ? (
              summary.deals_by_stage.map((stage) => (
                <li
                  key={stage.stage_id}
                  className="flex items-center justify-between text-sm text-white"
                >
                  <span>{stage.stage_name}</span>
                  <span className="font-medium">{stage.count}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-shell-muted">Нет сделок</li>
            )}
          </ul>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Требуют follow-up</p>
          <ul className="mt-3 space-y-2">
            {summary.follow_up.deals.length > 0 ? (
              summary.follow_up.deals.map((deal) => (
                <li
                  key={deal.deal_id}
                  className="flex items-center justify-between text-sm text-white"
                >
                  <span className="truncate pr-3">{deal.title}</span>
                  <span className="shrink-0 text-shell-muted">{deal.days_since_update} дн.</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-shell-muted">Нет просроченных открытых сделок</li>
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}
