"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import en from "./en";
import ru from "./ru";
import {
  DEFAULT_LOCALE,
  LOCALE_LABEL_KEYS,
  type Dictionary,
  type Locale,
  type TranslationKey,
} from "./types";

const dictionaries: Record<Locale, Dictionary> = { ru, en };

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
  localeOptions: Array<{ locale: Locale; label: string }>;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(DEFAULT_LOCALE);

  const t = useCallback(
    (key: TranslationKey) => dictionaries[locale][key] ?? key,
    [locale],
  );

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale,
      t,
      localeOptions: (Object.keys(dictionaries) as Locale[]).map((item) => ({
        locale: item,
        label: dictionaries[item][LOCALE_LABEL_KEYS[item]],
      })),
    }),
    [locale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }

  return context;
}
