import type { AuthProfile, LoginPayload } from "@/types/auth";
import { apiFetch } from "./client";

export async function fetchSession(cookieHeader?: string): Promise<AuthProfile | null> {
  try {
    return await apiFetch<AuthProfile>("/auth/me", { method: "GET" }, cookieHeader);
  } catch (error) {
    if (error instanceof Error && "status" in error && (error as { status: number }).status === 401) {
      return null;
    }

    throw error;
  }
}

export async function login(payload: LoginPayload): Promise<AuthProfile> {
  return apiFetch<AuthProfile>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
    credentials: "include",
  });
}

export async function logout(): Promise<void> {
  await apiFetch<{ status: string }>("/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}
