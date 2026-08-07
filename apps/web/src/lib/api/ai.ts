import { apiFetch } from "@/lib/api/client";

function aiPath(path: string): string {
  if (typeof window !== "undefined") {
    return `/api/ai${path}`;
  }

  return `/ai${path}`;
}

export type AiScore = {
  probability: number;
  label: string;
  rationale: string;
};

export type AiNextAction = {
  action: string;
  priority: "low" | "medium" | "high";
};

export type AiDraft = {
  subject: string | null;
  body: string;
  channel_hint: string;
};

export type AiInsight = {
  deal_id: string;
  provider_mode: "mock" | "live" | "degraded";
  advisory: boolean;
  score: AiScore;
  next_action: AiNextAction;
  draft_suggestion: AiDraft;
};

export type OrgAiRecommendation = {
  title: string;
  detail: string;
  priority: "low" | "medium" | "high";
};

export type OrgAiInsight = {
  provider_mode: "mock" | "live" | "degraded";
  advisory: boolean;
  health: AiScore;
  outlook: string;
  recommendations: OrgAiRecommendation[];
  planning: string;
};

export type AiStatus = {
  mode: "mock" | "live" | "disabled";
  reason: string;
  use_cases: string[];
};

export async function fetchAiStatus(cookieHeader?: string): Promise<AiStatus> {
  return apiFetch<AiStatus>(aiPath("/status"), { method: "GET" }, cookieHeader);
}

export async function fetchDealAiInsights(dealId: string, cookieHeader?: string): Promise<AiInsight> {
  return apiFetch<AiInsight>(aiPath(`/deals/${dealId}/insights`), { method: "GET" }, cookieHeader);
}

export async function fetchAnalyticsAiInsights(cookieHeader?: string): Promise<OrgAiInsight> {
  return apiFetch<OrgAiInsight>(aiPath("/analytics/insights"), { method: "GET" }, cookieHeader);
}
