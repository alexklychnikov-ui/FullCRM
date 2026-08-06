import { cookies } from "next/headers";

import { AnalyticsSummaryCards } from "@/components/analytics/AnalyticsSummaryCards";
import { DashboardHeader, DashboardInfoGrid } from "@/components/dashboard/DashboardInfoGrid";
import { fetchAnalyticsSummary } from "@/lib/api/analytics";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function DashboardPage() {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  const showAnalytics = hasModule(session, "analytics");
  let analyticsSummary = null;

  if (showAnalytics) {
    const cookieStore = await cookies();
    const cookieHeader = cookieStore
      .getAll()
      .map((item) => `${item.name}=${item.value}`)
      .join("; ");

    try {
      analyticsSummary = await fetchAnalyticsSummary(cookieHeader);
    } catch {
      analyticsSummary = null;
    }
  }

  return (
    <div className="space-y-6">
      <DashboardHeader session={session} />
      {analyticsSummary ? <AnalyticsSummaryCards summary={analyticsSummary} /> : null}
      <DashboardInfoGrid session={session} />
    </div>
  );
}
