import { apiFetch } from "@/lib/api/client";

function communicationsPath(path: string): string {
  if (typeof window !== "undefined") {
    return `/api/communications${path}`;
  }

  return `/communications${path}`;
}

export type Communication = {
  id: string;
  organization_id: string;
  thread_id: string;
  direction: string;
  channel_type: string;
  body: string | null;
  external_message_id: string | null;
  contact_id: string | null;
  company_id: string | null;
  deal_id: string | null;
  occurred_at: string;
};

export type IntegrationStatus = {
  channel: string;
  mode: string;
  reason: string;
};

export async function fetchCommunicationsTimeline(
  params: { contact_id?: string; company_id?: string; deal_id?: string },
  cookieHeader?: string,
) {
  const query = new URLSearchParams();

  if (params.contact_id) {
    query.set("contact_id", params.contact_id);
  }

  if (params.company_id) {
    query.set("company_id", params.company_id);
  }

  if (params.deal_id) {
    query.set("deal_id", params.deal_id);
  }

  const suffix = query.toString() ? `?${query.toString()}` : "";

  return apiFetch<Communication[]>(
    communicationsPath(`/timeline${suffix}`),
    {},
    cookieHeader,
  );
}

export async function fetchIntegrationsStatus(cookieHeader?: string) {
  return apiFetch<{ integrations: IntegrationStatus[] }>(
    communicationsPath("/integrations/status"),
    {},
    cookieHeader,
  );
}

export async function createCommunicationMessage(
  payload: {
    channel_type: string;
    direction?: string;
    body: string;
    contact_id?: string | null;
    company_id?: string | null;
    deal_id?: string | null;
  },
  cookieHeader?: string,
) {
  return apiFetch<Communication>(
    communicationsPath("/messages"),
    { method: "POST", body: JSON.stringify(payload) },
    cookieHeader,
  );
}
