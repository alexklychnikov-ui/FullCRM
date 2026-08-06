"use client";

import Link from "next/link";

import { useI18n } from "@/lib/i18n";
import {
  resolveDisplayFullName,
  resolveModuleName,
  resolveRoleName,
} from "@/lib/i18n/labels";
import type { AuthProfile } from "@/types/auth";

type DashboardInfoGridProps = {
  session: AuthProfile;
};

export function DashboardHeader({ session }: DashboardInfoGridProps) {
  const { t } = useI18n();

  return (
    <div>
      <h1 className="text-2xl font-semibold text-white">{t("dashboard.title")}</h1>
      <p className="text-sm text-shell-muted">
        {t("dashboard.welcome")}, {resolveDisplayFullName(session.user.fullName, t)}
      </p>
    </div>
  );
}

export function DashboardInfoGrid({ session }: DashboardInfoGridProps) {
  const { t } = useI18n();

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
        <p className="text-xs uppercase tracking-wide text-shell-muted">{t("dashboard.org")}</p>
        <p className="mt-2 text-lg font-medium text-white">{session.organization.name}</p>
        <p className="text-sm text-shell-muted">{session.user.email}</p>
      </section>

      <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
        <p className="text-xs uppercase tracking-wide text-shell-muted">{t("dashboard.roles")}</p>
        <ul className="mt-2 space-y-1 text-sm text-white">
          {session.roles.map((role) => (
            <li key={role}>{resolveRoleName(role, t)}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg border border-shell-border bg-shell-panel p-4">
        <p className="text-xs uppercase tracking-wide text-shell-muted">{t("dashboard.modules")}</p>
        <ul className="mt-2 space-y-1 text-sm text-white">
          {session.modules.length > 0 ? (
            session.modules.map((moduleKey) => (
              <li key={moduleKey}>{resolveModuleName(moduleKey, t)}</li>
            ))
          ) : (
            <li className="text-shell-muted">{t("dashboard.noModules")}</li>
          )}
        </ul>
        <p className="mt-3 text-xs text-shell-muted">
          {t("dashboard.modulesHint")}{" "}
          <Link className="text-shell-accent hover:underline" href="/settings?tab=modules">
            {t("dashboard.modulesManage")}
          </Link>
        </p>
      </section>
    </div>
  );
}
