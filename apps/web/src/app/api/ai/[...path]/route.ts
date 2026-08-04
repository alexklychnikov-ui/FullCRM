import { NextResponse } from "next/server";

import { proxyBackend } from "@/lib/api/proxy";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function handle(request: Request, context: RouteContext, method: string) {
  const { path } = await context.params;

  if (path.some((segment) => segment === ".." || segment.includes(".."))) {
    return NextResponse.json({ detail: "Invalid path" }, { status: 400 });
  }

  const suffix = path.join("/");
  const query = new URL(request.url).search;

  return proxyBackend(`/ai/${suffix}${query}`, request, method);
}

export async function GET(request: Request, context: RouteContext) {
  return handle(request, context, "GET");
}

export async function POST(request: Request, context: RouteContext) {
  return handle(request, context, "POST");
}
