import { NextResponse } from "next/server";

const DEFAULT_BACKEND_URL = "http://localhost:8000";

export function getBackendUrl(): string {
  return (
    process.env.API_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    DEFAULT_BACKEND_URL
  );
}

function normalizeSetCookie(cookie: string): string {
  return cookie
    .split(";")
    .map((part) => part.trim())
    .filter((part) => part.length > 0 && !/^domain=/i.test(part))
    .join("; ");
}

export async function proxyBackendAuth(
  path: string,
  request: Request,
  method: string,
): Promise<NextResponse> {
  return proxyBackend(path, request, method);
}

export async function proxyBackend(
  path: string,
  request: Request,
  method: string,
): Promise<NextResponse> {
  const cookieHeader = request.headers.get("cookie");
  const body =
    method === "GET" || method === "HEAD" ? undefined : await request.text();

  const backendResponse = await fetch(`${getBackendUrl()}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
    },
    body,
    cache: "no-store",
  });

  const responseBody = await backendResponse.text();
  const response = new NextResponse(responseBody, {
    status: backendResponse.status,
  });

  const contentType = backendResponse.headers.get("content-type");

  if (contentType) {
    response.headers.set("content-type", contentType);
  }

  for (const cookie of backendResponse.headers.getSetCookie()) {
    response.headers.append("Set-Cookie", normalizeSetCookie(cookie));
  }

  return response;
}
