import type { TranslationKey } from "@/lib/i18n/types";

export type AppModule = {
  key: string;
  href: string;
  labelKey: TranslationKey;
};

export const APP_MODULES: AppModule[] = [
  { key: "crm", href: "/crm", labelKey: "nav.crm" },
  { key: "communications", href: "/communications", labelKey: "nav.communications" },
];

export const PROTECTED_PREFIXES = [
  "/dashboard",
  "/settings",
  ...APP_MODULES.map((item) => item.href),
];

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function getModuleByPath(pathname: string): AppModule | undefined {
  return APP_MODULES.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  );
}
