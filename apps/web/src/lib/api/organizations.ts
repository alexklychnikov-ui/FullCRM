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

export type OrganizationModule = {
  module_key: string;
  enabled: boolean;
};

export type OrganizationModules = {
  modules: OrganizationModule[];
};

export async function fetchOrganizationModules(cookieHeader?: string) {
  return apiFetch<OrganizationModules>(
    organizationsPath("/me/modules"),
    {},
    cookieHeader,
  );
}

export async function updateOrganizationModules(
  payload: OrganizationModules,
  cookieHeader?: string,
) {
  return apiFetch<OrganizationModules>(
    organizationsPath("/me/modules"),
    { method: "PATCH", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export type OrganizationRole = {
  id: string;
  name: string;
  description: string | null;
};

export type OrganizationRoles = {
  roles: OrganizationRole[];
};

export type OrganizationUser = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
};

export type OrganizationUsers = {
  users: OrganizationUser[];
};

export type OrganizationUserCreatePayload = {
  email: string;
  full_name: string;
  password: string;
  roles: string[];
};

export async function fetchOrganizationRoles(cookieHeader?: string) {
  return apiFetch<OrganizationRoles>(organizationsPath("/me/roles"), {}, cookieHeader);
}

export async function fetchOrganizationUsers(cookieHeader?: string) {
  return apiFetch<OrganizationUsers>(organizationsPath("/me/users"), {}, cookieHeader);
}

export async function createOrganizationUser(
  payload: OrganizationUserCreatePayload,
  cookieHeader?: string,
) {
  return apiFetch<OrganizationUser>(
    organizationsPath("/me/users"),
    { method: "POST", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function patchOrganizationUser(
  userId: string,
  payload: { full_name?: string; is_active?: boolean; password?: string },
  cookieHeader?: string,
) {
  return apiFetch<OrganizationUser>(
    organizationsPath(`/me/users/${userId}`),
    { method: "PATCH", body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export async function putOrganizationUserRoles(
  userId: string,
  roles: string[],
  cookieHeader?: string,
) {
  return apiFetch<OrganizationUser>(
    organizationsPath(`/me/users/${userId}/roles`),
    { method: "PUT", body: JSON.stringify({ roles }) },
    cookieHeader,
  );
}
