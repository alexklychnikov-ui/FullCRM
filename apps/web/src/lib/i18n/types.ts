export type Locale = "ru" | "en";

export type TranslationKey =
  | "app.title"
  | "app.tagline"
  | "nav.dashboard"
  | "nav.crm"
  | "nav.communications"
  | "nav.logout"
  | "login.title"
  | "login.subtitle"
  | "login.email"
  | "login.password"
  | "login.submit"
  | "login.error"
  | "dashboard.title"
  | "dashboard.welcome"
  | "dashboard.org"
  | "dashboard.roles"
  | "dashboard.modules"
  | "module.disabled.title"
  | "module.disabled.body"
  | "locale.ru"
  | "locale.en";

export type Dictionary = Record<TranslationKey, string>;

export const DEFAULT_LOCALE: Locale = "ru";

export const LOCALE_LABEL_KEYS: Record<Locale, TranslationKey> = {
  ru: "locale.ru",
  en: "locale.en",
};
