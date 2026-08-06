import { apiFetch } from "@/lib/api/client";

function analyticsPath(path: string): string {
  if (typeof window !== "undefined") {
    return `/api/analytics${path}`;
  }

  return `/analytics${path}`;
}

export type StageCount = {
  stage_id: string;
  stage_name: string;
  count: number;
  amount_total: number | null;
};

export type ConversionMetrics = {
  total_deals: number;
  won_deals: number;
  open_deals: number;
  win_rate: number | null;
  currency: string;
  open_pipeline_amount: number | null;
  won_amount: number | null;
  avg_deal_amount: number | null;
};

export type CycleMetrics = {
  avg_days_to_close: number | null;
  won_sample_size: number;
};

export type ActivityMetrics = {
  total_events: number;
  events_last_7_days: number;
  activity_window_days: number;
};

export type FollowUpDeal = {
  deal_id: string;
  title: string;
  days_since_update: number;
  amount: number | null;
  currency: string;
  status: string;
  stage_name: string;
};

export type FollowUpMetrics = {
  stale_threshold_days: number;
  overdue_count: number;
  deals: FollowUpDeal[];
};

export type AnalyticsSummary = {
  computed_at: string;
  refresh_strategy: string;
  deals_by_stage: StageCount[];
  conversion: ConversionMetrics;
  cycle: CycleMetrics;
  activity: ActivityMetrics;
  follow_up: FollowUpMetrics;
};

export async function fetchAnalyticsSummary(cookieHeader?: string) {
  return apiFetch<AnalyticsSummary>(analyticsPath("/summary"), {}, cookieHeader);
}
