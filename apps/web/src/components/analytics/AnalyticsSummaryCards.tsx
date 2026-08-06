"use client";

import Link from "next/link";

import { useI18n } from "@/lib/i18n";
import { resolveDealStatus, resolveStageName } from "@/lib/i18n/labels";
import type { AnalyticsSummary } from "@/lib/api/analytics";

type AnalyticsSummaryCardsProps = {
  summary: AnalyticsSummary;
  showPageLink?: boolean;
};

function formatPercent(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

function formatMoney(value: number | null, currency: string): string {
  if (value === null) {
    return "—";
  }

  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 0 })} ${currency}`;
}

export function AnalyticsSummaryCards({
  summary,
  showPageLink = false,
}: AnalyticsSummaryCardsProps) {
  const { t, locale } = useI18n();
  const computedAt = new Date(summary.computed_at).toLocaleString(
    locale === "ru" ? "ru-RU" : "en-US",
  );
  const maxStageCount = Math.max(...summary.deals_by_stage.map((item) => item.count), 1);
  const currency = summary.conversion.currency || "RUB";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-medium text-white">{t("analytics.title")}</h2>
          <p className="text-xs text-shell-muted">
            {t("analytics.updated")}: {computedAt}
          </p>
        </div>
        {showPageLink ? (
          <Link className="text-sm text-shell-accent hover:underline" href="/analytics">
            {t("analytics.openPage")}
          </Link>
        ) : null}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
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
            {t("analytics.pipelineValue")}
          </p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {formatMoney(summary.conversion.open_pipeline_amount, currency)}
          </p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.wonAmount")}: {formatMoney(summary.conversion.won_amount, currency)}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">
            {t("analytics.conversionTitle")}
          </p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {formatPercent(summary.conversion.win_rate)}
          </p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.avgDeal")}: {formatMoney(summary.conversion.avg_deal_amount, currency)}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">
            {t("analytics.avgCycle")}
          </p>
          <p className="mt-2 text-2xl font-semibold text-white">
            {summary.cycle.avg_days_to_close !== null
              ? `${summary.cycle.avg_days_to_close} ${t("analytics.daysShort")}`
              : "—"}
          </p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.cycleSample")}: {summary.cycle.won_sample_size}
          </p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">{t("analytics.activity")}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.activity.total_events}</p>
          <p className="mt-1 text-sm text-shell-muted">
            {t("analytics.activityWindowPrefix")} {summary.activity.activity_window_days}{" "}
            {t("analytics.daysShort")}: {summary.activity.events_last_7_days}
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
          <ul className="mt-3 space-y-3">
            {summary.deals_by_stage.length > 0 ? (
              summary.deals_by_stage.map((stage) => (
                <li key={stage.stage_id} className="space-y-1">
                  <div className="flex items-center justify-between text-sm text-white">
                    <span>{resolveStageName(stage.stage_name, t)}</span>
                    <span className="font-medium">
                      {stage.count}
                      {stage.amount_total !== null
                        ? ` · ${formatMoney(stage.amount_total, currency)}`
                        : ""}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded bg-shell-bg">
                    <div
                      className="h-full rounded bg-shell-accent"
                      style={{ width: `${Math.max((stage.count / maxStageCount) * 100, 4)}%` }}
                    />
                  </div>
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
                <li key={deal.deal_id} className="text-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <Link
                        className="truncate text-white hover:underline"
                        href={`/crm/deals/${deal.deal_id}`}
                      >
                        {deal.title}
                      </Link>
                      <p className="text-xs text-shell-muted">
                        {resolveDealStatus(deal.status, t)} ·{" "}
                        {resolveStageName(deal.stage_name, t)}
                        {deal.amount !== null
                          ? ` · ${formatMoney(deal.amount, deal.currency)}`
                          : ""}
                      </p>
                    </div>
                    <span className="shrink-0 text-shell-muted">
                      {deal.days_since_update} {t("analytics.daysShort")}
                    </span>
                  </div>
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
