import { apiFetch } from "@/lib/api/client";

function organizationsPath(path: string): string {
  if (typeof window !== "undefined") {
    return `/api/organizations${path}`;
  }

  return `/organizations${path}`;
}

export type OrganizationSettings = {
  analytics: {
    stale_deal_days: number;
    activity_window_days: number;
  };
};

export async function fetchOrganizationSettings(cookieHeader?: string) {
  return apiFetch<OrganizationSettings>(
    organizationsPath("/me/settings"),
    {},
    cookieHeader,
  );
}

export async function updateOrganizationSettings(
  payload: OrganizationSettings,
  cookieHeader?: string,
) {
  return apiFetch<OrganizationSettings>(
    organizationsPath("/me/settings"),
    { method: "PATCH", body: JSON.stringify(payload) },
    cookieHeader,
  );
}
