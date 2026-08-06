"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { OrganizationModule } from "@/lib/api/organizations";
import { updateOrganizationModules } from "@/lib/api/organizations";
import { useI18n } from "@/lib/i18n";
import { resolveModuleName } from "@/lib/i18n/labels";

type OrganizationModulesFormProps = {
  modules: OrganizationModule[];
};

export function OrganizationModulesForm({ modules }: OrganizationModulesFormProps) {
  const router = useRouter();
  const { t } = useI18n();
  const [enabledByKey, setEnabledByKey] = useState(() =>
    Object.fromEntries(modules.map((item) => [item.module_key, item.enabled])),
  );
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  function toggleModule(moduleKey: string, enabled: boolean) {
    if (moduleKey === "crm") {
      return;
    }

    setEnabledByKey((current) => ({ ...current, [moduleKey]: enabled }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      await updateOrganizationModules({
        modules: modules.map((item) => ({
          module_key: item.module_key,
          enabled: enabledByKey[item.module_key] ?? item.enabled,
        })),
      });
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("settings.saveError"));
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="max-w-lg space-y-4" onSubmit={handleSubmit}>
      <p className="text-sm text-shell-muted">{t("settings.modulesHint")}</p>

      <ul className="space-y-3">
        {modules.map((item) => {
          const isCrm = item.module_key === "crm";
          const enabled = enabledByKey[item.module_key] ?? item.enabled;

          return (
            <li
              key={item.module_key}
              className="flex items-center justify-between rounded-md border border-shell-border bg-shell-panel px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-white">
                  {resolveModuleName(item.module_key, t)}
                </p>
                {isCrm ? (
                  <p className="text-xs text-shell-muted">{t("settings.modulesCrmLocked")}</p>
                ) : null}
              </div>
              <input
                checked={enabled}
                className="h-4 w-4 accent-shell-accent disabled:opacity-60"
                disabled={isCrm || pending}
                type="checkbox"
                onChange={(event) => toggleModule(item.module_key, event.target.checked)}
              />
            </li>
          );
        })}
      </ul>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <button
        className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        disabled={pending}
        type="submit"
      >
        {pending ? t("settings.saving") : t("settings.modulesSave")}
      </button>
    </form>
  );
}
