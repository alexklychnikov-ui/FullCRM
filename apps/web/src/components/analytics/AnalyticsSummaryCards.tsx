"use client";

import { useI18n } from "@/lib/i18n";
import { resolveStageName } from "@/lib/i18n/labels";
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
  const { t, locale } = useI18n();
  const computedAt = new Date(summary.computed_at).toLocaleString(
    locale === "ru" ? "ru-RU" : "en-US",
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium text-white">{t("analytics.title")}</h2>
        <p className="text-xs text-shell-muted">
          {t("analytics.updated")}: {computedAt}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">{t("analytics.deals")}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.conversion.total_deals}</p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.openDeals")}: {summary.conversion.open_deals} · {t("analytics.wonDeals")}:{" "}
            {summary.conversion.won_deals}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">
            {t("analytics.conversionTitle")}
          </p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {formatPercent(summary.conversion.win_rate)}
          </p>
          <p className="mt-1 text-sm text-shell-muted">{t("analytics.conversionHint")}</p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">{t("analytics.activity")}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.activity.total_events}</p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.activityLast7")}: {summary.activity.events_last_7_days}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">
            {t("analytics.overdueFollowUp")}
          </p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.follow_up.overdue_count}</p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.staleDaysPrefix")} {summary.follow_up.stale_threshold_days}{" "}
            {t("analytics.staleDaysSuffix")}
          </p>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">
            {t("analytics.dealsByStage")}
          </p>
          <ul className="mt-3 space-y-2">
            {summary.deals_by_stage.length > 0 ? (
              summary.deals_by_stage.map((stage) => (
                <li
                  key={stage.stage_id}
                  className="flex items-center justify-between text-sm text-white"
                >
                  <span>{resolveStageName(stage.stage_name, t)}</span>
                  <span className="font-medium">{stage.count}</span>
                </li>
              ))
            ) : (
              <li className="text-sm text-shell-muted">{t("analytics.noDeals")}</li>
            )}
          </ul>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">
            {t("analytics.requiresFollowUp")}
          </p>
          <ul className="mt-3 space-y-2">
            {summary.follow_up.deals.length > 0 ? (
              summary.follow_up.deals.map((deal) => (
                <li
                  key={deal.deal_id}
                  className="flex items-center justify-between text-sm text-white"
                >
                  <span className="truncate pr-3">{deal.title}</span>
                  <span className="shrink-0 text-shell-muted">
                    {deal.days_since_update} {t("analytics.daysShort")}
                  </span>
                </li>
              ))
            ) : (
              <li className="text-sm text-shell-muted">{t("analytics.noOverdueDeals")}</li>
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}
