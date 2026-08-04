"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useI18n } from "@/lib/i18n";
import { APP_MODULES } from "@/lib/modules/config";
import type { AuthProfile } from "@/types/auth";

type SidebarProps = {
  session: AuthProfile;
};

export function Sidebar({ session }: SidebarProps) {
  const pathname = usePathname();
  const { t } = useI18n();

  const visibleModules = APP_MODULES.filter((item) => session.modules.includes(item.key));

  const navItems = [
    { href: "/dashboard", label: t("nav.dashboard"), gated: false },
    ...visibleModules.map((item) => ({
      href: item.href,
      label: t(item.labelKey),
      gated: true,
    })),
  ];

  return (
    <aside className="flex w-64 flex-col border-r border-shell-border bg-shell-panel">
      <div className="border-b border-shell-border px-5 py-4">
        <p className="text-lg font-semibold text-white">{t("app.title")}</p>
        <p className="text-xs text-shell-muted">{session.organization.name}</p>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              className={`block rounded-md px-3 py-2 text-sm transition ${
                active
                  ? "bg-shell-accent/20 text-white"
                  : "text-shell-muted hover:bg-shell-bg hover:text-white"
              }`}
              href={item.href}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
