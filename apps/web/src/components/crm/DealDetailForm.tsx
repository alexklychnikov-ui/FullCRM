"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Assignee, Company, Contact, Deal, PipelineStage } from "@/lib/api/crm";
import { transitionDeal, updateDeal } from "@/lib/api/crm";

type DealDetailFormProps = {
  deal: Deal;
  pipelineStages: PipelineStage[];
  companies: Company[];
  contacts: Contact[];
  assignees: Assignee[];
};

export function DealDetailForm({
  deal,
  pipelineStages,
  companies,
  contacts,
  assignees,
}: DealDetailFormProps) {
  const router = useRouter();
  const [title, setTitle] = useState(deal.title);
  const [amount, setAmount] = useState(deal.amount ?? "");
  const [status, setStatus] = useState(deal.status);
  const [companyId, setCompanyId] = useState(deal.company_id ?? "");
  const [contactId, setContactId] = useState(deal.contact_id ?? "");
  const [ownerUserId, setOwnerUserId] = useState(deal.owner_user_id ?? "");
  const [stageId, setStageId] = useState(deal.stage_id);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      await updateDeal(deal.id, {
        title,
        amount: amount || null,
        status,
        company_id: companyId || null,
        contact_id: contactId || null,
        owner_user_id: ownerUserId || null,
      });

      if (stageId !== deal.stage_id) {
        await transitionDeal(deal.id, stageId);
      }

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
        <span className="mb-1 block text-shell-muted">Название</span>
        <input
          required
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">Этап воронки</span>
        <select
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          value={stageId}
          onChange={(event) => setStageId(event.target.value)}
        >
          {pipelineStages.map((stage) => (
            <option key={stage.id} value={stage.id}>
              {stage.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">Статус</span>
        <input
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        />
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">Сумма</span>
        <input
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
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
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">Контакт</span>
        <select
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          value={contactId}
          onChange={(event) => setContactId(event.target.value)}
        >
          <option value="">Без контакта</option>
          {contacts.map((contact) => (
            <option key={contact.id} value={contact.id}>
              {contact.full_name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-shell-muted">Ответственный</span>
        <select
          className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
          value={ownerUserId}
          onChange={(event) => setOwnerUserId(event.target.value)}
        >
          {assignees.map((assignee) => (
            <option key={assignee.id} value={assignee.id}>
              {assignee.full_name}
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
