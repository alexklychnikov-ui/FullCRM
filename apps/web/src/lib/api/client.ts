const DEFAULT_API_URL = "http://localhost:8000";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getApiBaseUrl(): string {
  if (isBrowser()) {
    return "";
  }

  return (
    process.env.API_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    DEFAULT_API_URL
  );
}

export function getAuthPath(path: string): string {
  if (isBrowser()) {
    return `/api/auth${path.replace("/auth", "")}`;
  }

  return path;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  cookieHeader?: string,
): Promise<T> {
  const headers = new Headers(init.headers);

  if (cookieHeader) {
    headers.set("cookie", cookieHeader);
  }

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const requestPath =
    isBrowser() && path.startsWith("/auth") ? getAuthPath(path) : path;

  const response = await fetch(`${getApiBaseUrl()}${requestPath}`, {
    ...init,
    headers,
    credentials: init.credentials ?? "include",
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = response.statusText;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // ignore parse errors
    }

    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
