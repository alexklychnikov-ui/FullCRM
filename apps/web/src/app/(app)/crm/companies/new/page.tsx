"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { CrmNav } from "@/components/crm/CrmNav";
import { createCompany } from "@/lib/api/crm";

export default function NewCompanyPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const company = await createCompany({
        name,
        domain: domain || null,
      });
      router.push(`/crm/companies/${company.id}`);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Ошибка сохранения");
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Новая компания</h1>
      <CrmNav active="companies" />
      <form className="max-w-lg space-y-4" onSubmit={handleSubmit}>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Название</span>
          <input
            required
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Домен</span>
          <input
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={domain}
            onChange={(event) => setDomain(event.target.value)}
          />
        </label>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <button
          className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          disabled={pending}
          type="submit"
        >
          {pending ? "Сохранение..." : "Создать"}
        </button>
      </form>
    </div>
  );
}
