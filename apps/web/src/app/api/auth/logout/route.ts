import { proxyBackendAuth } from "@/lib/api/proxy";

export async function POST(request: Request) {
  return proxyBackendAuth("/auth/logout", request, "POST");
}
