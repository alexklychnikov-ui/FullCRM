"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { IntegrationStatusPanel } from "@/components/communications/IntegrationStatusPanel";
import type { IntegrationStatus } from "@/lib/api/communications";
import { pollTelegram } from "@/lib/api/communications";
import { useI18n } from "@/lib/i18n";

type SettingsIntegrationsPanelProps = {
  integrations: IntegrationStatus[];
};

export function SettingsIntegrationsPanel({ integrations }: SettingsIntegrationsPanelProps) {
  const router = useRouter();
  const { t } = useI18n();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState("");

  const telegramLive = integrations.some(
    (item) => item.channel === "telegram" && item.mode === "live",
  );

  async function handlePoll() {
    setPending(true);
    setError("");
    setResult("");

    try {
      const response = await pollTelegram();
      setResult(
        t("settings.integrations.pollResult")
          .replace("{processed}", String(response.processed))
          .replace("{created}", String(response.created))
          .replace("{skipped}", String(response.skipped_unmatched)),
      );
      router.refresh();
    } catch (pollError) {
      setError(
        pollError instanceof Error ? pollError.message : t("settings.integrations.pollError"),
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-4">
      <IntegrationStatusPanel integrations={integrations} />

      <div className="rounded-md border border-shell-border bg-shell-panel p-4">
        <p className="text-sm text-shell-muted">{t("settings.integrations.pollHint")}</p>
        <button
          className="mt-3 rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          disabled={!telegramLive || pending}
          type="button"
          onClick={handlePoll}
        >
          {pending ? t("settings.integrations.polling") : t("settings.integrations.poll")}
        </button>
        {!telegramLive ? (
          <p className="mt-2 text-xs text-amber-400">{t("settings.integrations.pollDisabled")}</p>
        ) : null}
        {result ? <p className="mt-2 text-sm text-emerald-400">{result}</p> : null}
        {error ? <p className="mt-2 text-sm text-red-400">{error}</p> : null}
      </div>
    </div>
  );
}
