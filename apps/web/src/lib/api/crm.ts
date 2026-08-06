import { apiFetch } from "@/lib/api/client";

function crmPath(path: string): string {
  if (typeof window !== "undefined") {
    return `/api/crm${path}`;
  }

  return `/crm${path}`;
}

export type Company = {
  id: string;
  organization_id: string;
  name: string;
  domain: string | null;
  created_at: string;
  updated_at: string;
};

export type Contact = {
  id: string;
  organization_id: string;
  company_id: string | null;
  full_name: string;
  email: string | null;
  phone: string | null;
  telegram_chat_id: string | null;
  created_at: string;
  updated_at: string;
};

export type PipelineStage = {
  id: string;
  pipeline_id: string;
  name: string;
  position: number;
  probability: number;
};

export type Pipeline = {
  id: string;
  organization_id: string;
  name: string;
  is_default: boolean;
  stages: PipelineStage[];
};

export type Deal = {
  id: string;
  organization_id: string;
  pipeline_id: string;
  stage_id: string;
  company_id: string | null;
  contact_id: string | null;
  title: string;
  amount: string | null;
  currency: string;
  status: string;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type Assignee = {
  id: string;
  full_name: string;
  email: string;
};

export type EventLog = {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  actor_user_id: string | null;
  payload: Record<string, unknown>;
  recorded_at: string;
};

export async function fetchCompanies(cookieHeader?: string) {
  return apiFetch<Company[]>(crmPath("/companies"), {}, cookieHeader);
}

export async function fetchCompany(id: string, cookieHeader?: string) {
  return apiFetch<Company>(crmPath(`/companies/${id}`), {}, cookieHeader);
}

export async function createCompany(
  payload: { name: string; domain?: string | null },
  cookieHeader?: string,
) {
  return apiFetch<Company>(
    crmPath("/companies"),
    { method: "POST", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function updateCompany(
  id: string,
  payload: { name?: string; domain?: string | null },
  cookieHeader?: string,
) {
  return apiFetch<Company>(
    crmPath(`/companies/${id}`),
    { method: "PATCH", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function fetchContacts(cookieHeader?: string) {
  return apiFetch<Contact[]>(crmPath("/contacts"), {}, cookieHeader);
}

export async function fetchContact(id: string, cookieHeader?: string) {
  return apiFetch<Contact>(crmPath(`/contacts/${id}`), {}, cookieHeader);
}

export async function createContact(
  payload: {
    full_name: string;
    email?: string | null;
    phone?: string | null;
    company_id?: string | null;
    telegram_chat_id?: string | null;
  },
  cookieHeader?: string,
) {
  return apiFetch<Contact>(
    crmPath("/contacts"),
    { method: "POST", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function updateContact(
  id: string,
  payload: {
    full_name?: string;
    email?: string | null;
    phone?: string | null;
    company_id?: string | null;
    telegram_chat_id?: string | null;
  },
  cookieHeader?: string,
) {
  return apiFetch<Contact>(
    crmPath(`/contacts/${id}`),
    { method: "PATCH", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function fetchDeals(cookieHeader?: string) {
  return apiFetch<Deal[]>(crmPath("/deals"), {}, cookieHeader);
}

export async function fetchDeal(id: string, cookieHeader?: string) {
  return apiFetch<Deal>(crmPath(`/deals/${id}`), {}, cookieHeader);
}

export async function createDeal(
  payload: {
    title: string;
    pipeline_id: string;
    stage_id: string;
    company_id?: string | null;
    contact_id?: string | null;
    amount?: string | null;
    currency?: string;
    status?: string;
    owner_user_id?: string | null;
  },
  cookieHeader?: string,
) {
  return apiFetch<Deal>(
    crmPath("/deals"),
    { method: "POST", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function updateDeal(
  id: string,
  payload: {
    title?: string;
    company_id?: string | null;
    contact_id?: string | null;
    amount?: string | null;
    currency?: string;
    status?: string;
    owner_user_id?: string | null;
  },
  cookieHeader?: string,
) {
  return apiFetch<Deal>(
    crmPath(`/deals/${id}`),
    { method: "PATCH", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function transitionDeal(
  id: string,
  stageId: string,
  cookieHeader?: string,
) {
  return apiFetch<Deal>(
    crmPath(`/deals/${id}/transition`),
    { method: "POST", body: JSON.stringify({ stage_id: stageId }) },
    cookieHeader,
  );
}

export async function fetchPipelines(cookieHeader?: string) {
  return apiFetch<Pipeline[]>(crmPath("/pipelines"), {}, cookieHeader);
}

export async function fetchAssignees(cookieHeader?: string) {
  return apiFetch<Assignee[]>(crmPath("/assignees"), {}, cookieHeader);
}

export async function fetchEventLogs(
  params: { entity_type?: string; entity_id?: string },
  cookieHeader?: string,
) {
  const query = new URLSearchParams();

  if (params.entity_type) {
    query.set("entity_type", params.entity_type);
  }

  if (params.entity_id) {
    query.set("entity_id", params.entity_id);
  }

  const suffix = query.toString() ? `?${query.toString()}` : "";

  return apiFetch<EventLog[]>(crmPath(`/event-logs${suffix}`), {}, cookieHeader);
}
