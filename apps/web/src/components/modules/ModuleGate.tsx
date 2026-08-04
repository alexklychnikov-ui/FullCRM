"use client";

import { useI18n } from "@/lib/i18n";

export function ModuleDisabledState() {
  const { t } = useI18n();

  return (
    <div className="rounded-lg border border-shell-border bg-shell-panel p-6">
      <h1 className="text-xl font-semibold text-white">{t("module.disabled.title")}</h1>
      <p className="mt-2 text-sm text-shell-muted">{t("module.disabled.body")}</p>
    </div>
  );
}
