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
};

export type ConversionMetrics = {
  total_deals: number;
  won_deals: number;
  open_deals: number;
  win_rate: number | null;
};

export type ActivityMetrics = {
  total_events: number;
  events_last_7_days: number;
};

export type FollowUpDeal = {
  deal_id: string;
  title: string;
  days_since_update: number;
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
  activity: ActivityMetrics;
  follow_up: FollowUpMetrics;
};

export async function fetchAnalyticsSummary(cookieHeader?: string) {
  return apiFetch<AnalyticsSummary>(analyticsPath("/summary"), {}, cookieHeader);
}
