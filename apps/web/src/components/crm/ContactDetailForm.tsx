"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Company, Contact } from "@/lib/api/crm";
import { updateContact } from "@/lib/api/crm";

type ContactDetailFormProps = {
  contact: Contact;
  companies: Company[];
};

export function ContactDetailForm({ contact, companies }: ContactDetailFormProps) {
  const router = useRouter();
  const [fullName, setFullName] = useState(contact.full_name);
  const [email, setEmail] = useState(contact.email ?? "");
  const [phone, setPhone] = useState(contact.phone ?? "");
  const [companyId, setCompanyId] = useState(contact.company_id ?? "");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      await updateContact(contact.id, {
        full_name: fullName,
        email: email || null,
        phone: phone || null,
        company_id: companyId || null,
      });
      router.refresh();
      setPending(false);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Ошибка сохранения");
      setPending(false);
    }
  }

  return (
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
        {pending ? "Сохранение..." : "Сохранить"}
      </button>
    </form>
  );
}
