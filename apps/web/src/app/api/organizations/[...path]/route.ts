import { proxyBackend } from "@/lib/api/proxy";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function handle(request: Request, context: RouteContext, method: string) {
  const { path } = await context.params;
  const suffix = path.join("/");
  const query = new URL(request.url).search;

  return proxyBackend(`/organizations/${suffix}${query}`, request, method);
}

export async function GET(request: Request, context: RouteContext) {
  return handle(request, context, "GET");
}

export async function POST(request: Request, context: RouteContext) {
  return handle(request, context, "POST");
}

export async function PATCH(request: Request, context: RouteContext) {
  return handle(request, context, "PATCH");
}

export async function PUT(request: Request, context: RouteContext) {
  return handle(request, context, "PUT");
}

export async function DELETE(request: Request, context: RouteContext) {
  return handle(request, context, "DELETE");
}
