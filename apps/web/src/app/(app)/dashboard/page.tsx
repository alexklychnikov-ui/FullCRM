import { cookies } from "next/headers";

import { AnalyticsSummaryCards } from "@/components/analytics/AnalyticsSummaryCards";
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
      <div>
        <h1 className="text-2xl font-semibold text-white">Обзор</h1>
        <p className="text-sm text-shell-muted">
          Добро пожаловать, {session.user.fullName}
        </p>
      </div>

      {analyticsSummary ? <AnalyticsSummaryCards summary={analyticsSummary} /> : null}

      <div className="grid gap-4 md:grid-cols-3">
        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Организация</p>
          <p className="mt-2 text-lg font-medium text-white">{session.organization.name}</p>
          <p className="text-sm text-shell-muted">{session.user.email}</p>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Роли</p>
          <ul className="mt-2 space-y-1 text-sm text-white">
            {session.roles.map((role) => (
              <li key={role}>{role}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
          <p className="text-xs uppercase tracking-wide text-shell-muted">Активные модули</p>
          <ul className="mt-2 space-y-1 text-sm text-white">
            {session.modules.length > 0 ? (
              session.modules.map((moduleKey) => <li key={moduleKey}>{moduleKey}</li>)
            ) : (
              <li className="text-shell-muted">Нет активных модулей</li>
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}
