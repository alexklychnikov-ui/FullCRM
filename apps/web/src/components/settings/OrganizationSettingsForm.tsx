"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { OrganizationSettings } from "@/lib/api/organizations";
import { updateOrganizationSettings } from "@/lib/api/organizations";
import { useI18n } from "@/lib/i18n";

type OrganizationSettingsFormProps = {
  settings: OrganizationSettings;
};

export function OrganizationSettingsForm({ settings }: OrganizationSettingsFormProps) {
  const router = useRouter();
  const { t } = useI18n();
  const [staleDealDays, setStaleDealDays] = useState(settings.analytics.stale_deal_days);
  const [activityWindowDays, setActivityWindowDays] = useState(
    settings.analytics.activity_window_days,
  );
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      await updateOrganizationSettings({
        analytics: {
          stale_deal_days: staleDealDays,
          activity_window_days: activityWindowDays,
        },
      });
      router.refresh();
      setPending(false);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : t("settings.saveError"));
      setPending(false);
    }
  }

  return (
    <form className="max-w-lg space-y-4" onSubmit={handleSubmit}>
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">{t("settings.staleDealDays")}</span>
        <input
          required
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          min={1}
          max={365}
          type="number"
          value={staleDealDays}
          onChange={(event) => setStaleDealDays(Number(event.target.value))}
        />
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">{t("settings.activityWindowDays")}</span>
        <input
          required
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          min={1}
          max={365}
          type="number"
          value={activityWindowDays}
          onChange={(event) => setActivityWindowDays(Number(event.target.value))}
        />
      </label>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      <button
        className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        disabled={pending}
        type="submit"
      >
        {pending ? t("settings.saving") : t("settings.save")}
      </button>
    </form>
  );
}
