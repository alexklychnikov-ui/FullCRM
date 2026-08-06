"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { CrmNav } from "@/components/crm/CrmNav";
import type { Company } from "@/lib/api/crm";
import { createContact } from "@/lib/api/crm";

type NewContactPageProps = {
  companies: Company[];
};

export function NewContactForm({ companies }: NewContactPageProps) {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const contact = await createContact({
        full_name: fullName,
        email: email || null,
        phone: phone || null,
        company_id: companyId || null,
        telegram_chat_id: telegramChatId || null,
      });
      router.push(`/crm/contacts/${contact.id}`);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Ошибка сохранения");
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Новый контакт</h1>
      <CrmNav active="contacts" />
      <form className="max-w-lg space-y-4" onSubmit={handleSubmit}>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Имя</span>
          <input
            required
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Email</span>
          <input
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Телефон</span>
          <input
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">ID чата Telegram</span>
          <input
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={telegramChatId}
            onChange={(event) => setTelegramChatId(event.target.value)}
          />
          <span className="mt-1 block text-xs text-shell-muted">
            Для сопоставления сообщений Telegram
          </span>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Компания</span>
          <select
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={companyId}
            onChange={(event) => setCompanyId(event.target.value)}
          >
            <option value="">Без компании</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </select>
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
