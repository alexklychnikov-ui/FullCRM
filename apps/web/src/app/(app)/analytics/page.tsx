import { cookies } from "next/headers";

import { AnalyticsAiAdvisoryPanel } from "@/components/ai/AnalyticsAiAdvisoryPanel";
import { AnalyticsSummaryCards } from "@/components/analytics/AnalyticsSummaryCards";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchAiStatus } from "@/lib/api/ai";
import { fetchAnalyticsSummary } from "@/lib/api/analytics";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function AnalyticsPage() {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  if (!hasModule(session, "analytics")) {
    return <ModuleDisabledState />;
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");

  let summary = null;
  let aiStatus = null;
  const showAi = hasModule(session, "ai");

  try {
    summary = await fetchAnalyticsSummary(cookieHeader);
  } catch {
    summary = null;
  }

  if (showAi) {
    try {
      aiStatus = await fetchAiStatus(cookieHeader);
    } catch {
      aiStatus = null;
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Аналитика</h1>
        <p className="text-sm text-shell-muted">
          Воронка, деньги, цикл закрытия и сделки, требующие внимания
        </p>
      </div>

      {showAi ? <AnalyticsAiAdvisoryPanel initialStatus={aiStatus} /> : null}

      {summary ? (
        <AnalyticsSummaryCards summary={summary} />
      ) : (
        <p className="text-sm text-shell-muted">Не удалось загрузить аналитику.</p>
      )}
    </div>
  );
}
