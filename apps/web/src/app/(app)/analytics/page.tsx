import { cookies } from "next/headers";

import { AnalyticsSummaryCards } from "@/components/analytics/AnalyticsSummaryCards";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
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

  try {
    summary = await fetchAnalyticsSummary(cookieHeader);
  } catch {
    summary = null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Аналитика</h1>
        <p className="text-sm text-shell-muted">
          Воронка, деньги, цикл закрытия и сделки, требующие внимания
        </p>
      </div>

      {summary ? (
        <AnalyticsSummaryCards summary={summary} />
      ) : (
        <p className="text-sm text-shell-muted">Не удалось загрузить аналитику.</p>
      )}
    </div>
  );
}
