import { proxyBackendAuth } from "@/lib/api/proxy";

export async function GET(request: Request) {
  return proxyBackendAuth("/auth/me", request, "GET");
}
