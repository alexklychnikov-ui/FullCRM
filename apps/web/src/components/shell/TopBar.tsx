"use client";

import { useRouter } from "next/navigation";

import { logout } from "@/lib/api/auth";
import { useI18n } from "@/lib/i18n";
import type { AuthProfile } from "@/types/auth";

type TopBarProps = {
  session: AuthProfile;
};

export function TopBar({ session }: TopBarProps) {
  const router = useRouter();
  const { locale, setLocale, localeOptions, t } = useI18n();

  async function handleLogout() {
    await logout();
    router.replace("/login");
    router.refresh();
  }

  return (
    <header className="flex items-center justify-between border-b border-shell-border bg-shell-panel px-6 py-3">
      <div>
        <p className="text-sm text-shell-muted">{t("dashboard.welcome")}</p>
        <p className="font-medium text-white">{session.user.fullName}</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex rounded-md border border-shell-border p-0.5">
          {localeOptions.map((option) => (
            <button
              key={option.locale}
              className={`rounded px-2 py-1 text-xs ${
                locale === option.locale
                  ? "bg-shell-accent text-white"
                  : "text-shell-muted hover:text-white"
              }`}
              type="button"
              onClick={() => setLocale(option.locale)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <button
          className="rounded-md border border-shell-border px-3 py-1.5 text-sm text-shell-muted transition hover:border-red-400 hover:text-red-300"
          type="button"
          onClick={() => void handleLogout()}
        >
          {t("nav.logout")}
        </button>
      </div>
    </header>
  );
}
