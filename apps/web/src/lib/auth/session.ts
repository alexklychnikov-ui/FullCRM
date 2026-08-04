import { cookies } from "next/headers";

import { fetchSession } from "@/lib/api/auth";
import type { AuthProfile } from "@/types/auth";

export async function getServerSession(): Promise<AuthProfile | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");

  if (!cookieHeader) {
    return null;
  }

  return fetchSession(cookieHeader);
}

export function hasModule(session: AuthProfile, moduleKey: string): boolean {
  return session.modules.includes(moduleKey);
}
