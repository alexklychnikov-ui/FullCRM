"use client";

import Link from "next/link";

import { useI18n } from "@/lib/i18n";
import type { TranslationKey } from "@/lib/i18n/types";

export type SettingsTab = "analytics" | "integrations" | "modules";

type SettingsTabsProps = {
  activeTab: SettingsTab;
};

const TABS: { id: SettingsTab; labelKey: TranslationKey }[] = [
  { id: "analytics", labelKey: "settings.tab.analytics" },
  { id: "integrations", labelKey: "settings.tab.integrations" },
  { id: "modules", labelKey: "settings.tab.modules" },
];

export function SettingsTabs({ activeTab }: SettingsTabsProps) {
  const { t } = useI18n();

  return (
    <nav className="flex flex-wrap gap-2 border-b border-shell-border pb-3">
      {TABS.map((tab) => {
        const isActive = tab.id === activeTab;

        return (
          <Link
            key={tab.id}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              isActive
                ? "bg-shell-accent text-white"
                : "text-shell-muted hover:bg-shell-panel hover:text-white"
            }`}
            href={`/settings?tab=${tab.id}`}
          >
            {t(tab.labelKey)}
          </Link>
        );
      })}
    </nav>
  );
}
