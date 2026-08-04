import { NextResponse } from "next/server";

import { proxyBackend } from "@/lib/api/proxy";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function handle(request: Request, context: RouteContext, method: string) {
  const { path } = await context.params;
  const suffix = path.join("/");
  const query = new URL(request.url).search;

  return proxyBackend(`/analytics/${suffix}${query}`, request, method);
}

export async function GET(request: Request, context: RouteContext) {
  return handle(request, context, "GET");
}
