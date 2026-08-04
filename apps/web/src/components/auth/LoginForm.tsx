"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { login } from "@/lib/api/auth";
import { useI18n } from "@/lib/i18n";

type LoginFormProps = {
  nextPath: string;
};

export function LoginForm({ nextPath }: LoginFormProps) {
  const router = useRouter();
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);

    try {
      await login({ email: email.trim().toLowerCase(), password });
      router.replace(nextPath);
      router.refresh();
    } catch (submitError) {
      if (submitError instanceof ApiError && submitError.status === 401) {
        setError(t("login.error"));
      } else {
        setError(submitError instanceof Error ? submitError.message : t("login.error"));
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <label className="block space-y-1">
        <span className="text-sm text-shell-muted">{t("login.email")}</span>
        <input
          autoComplete="email"
          className="w-full rounded-md border border-shell-border bg-shell-bg px-3 py-2 text-white outline-none focus:border-shell-accent"
          name="email"
          required
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>

      <label className="block space-y-1">
        <span className="text-sm text-shell-muted">{t("login.password")}</span>
        <input
          autoComplete="current-password"
          className="w-full rounded-md border border-shell-border bg-shell-bg px-3 py-2 text-white outline-none focus:border-shell-accent"
          name="password"
          required
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <button
        className="w-full rounded-md bg-shell-accent px-4 py-2 font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        disabled={pending}
        type="submit"
      >
        {t("login.submit")}
      </button>
    </form>
  );
}
