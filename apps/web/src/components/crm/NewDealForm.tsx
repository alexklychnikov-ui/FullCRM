"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { CrmNav } from "@/components/crm/CrmNav";
import type { Assignee, Company, Contact, Pipeline } from "@/lib/api/crm";
import { createDeal } from "@/lib/api/crm";
import { useI18n } from "@/lib/i18n";
import { resolveDealStatus, resolveStageName } from "@/lib/i18n/labels";

type NewDealFormProps = {
  pipelines: Pipeline[];
  companies: Company[];
  contacts: Contact[];
  assignees: Assignee[];
  defaultOwnerId: string;
};

export function NewDealForm({
  pipelines,
  companies,
  contacts,
  assignees,
  defaultOwnerId,
}: NewDealFormProps) {
  const router = useRouter();
  const { t } = useI18n();
  const defaultPipeline = pipelines.find((pipeline) => pipeline.is_default) ?? pipelines[0];
  const [pipelineId, setPipelineId] = useState(defaultPipeline?.id ?? "");
  const [stageId, setStageId] = useState(defaultPipeline?.stages[0]?.id ?? "");
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [status, setStatus] = useState("open");
  const [companyId, setCompanyId] = useState("");
  const [contactId, setContactId] = useState("");
  const [ownerUserId, setOwnerUserId] = useState(defaultOwnerId);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const selectedPipeline = useMemo(
    () => pipelines.find((pipeline) => pipeline.id === pipelineId),
    [pipelineId, pipelines],
  );

  function handlePipelineChange(nextPipelineId: string) {
    setPipelineId(nextPipelineId);
    const pipeline = pipelines.find((item) => item.id === nextPipelineId);
    setStageId(pipeline?.stages[0]?.id ?? "");
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const deal = await createDeal({
        title,
        pipeline_id: pipelineId,
        stage_id: stageId,
        company_id: companyId || null,
        contact_id: contactId || null,
        amount: amount || null,
        status,
        owner_user_id: ownerUserId || null,
      });
      router.push(`/crm/deals/${deal.id}`);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Ошибка сохранения");
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Новая сделка</h1>
      <CrmNav active="deals" />
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
          <span className="mb-1 block text-shell-muted">Воронка</span>
          <select
            required
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={pipelineId}
            onChange={(event) => handlePipelineChange(event.target.value)}
          >
            {pipelines.map((pipeline) => (
              <option key={pipeline.id} value={pipeline.id}>
                {pipeline.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Этап</span>
          <select
            required
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={stageId}
            onChange={(event) => setStageId(event.target.value)}
          >
            {selectedPipeline?.stages.map((stage) => (
              <option key={stage.id} value={stage.id}>
                {resolveStageName(stage.name, t)}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-shell-muted">Статус</span>
          <select
            className="w-full rounded-md border border-shell-border bg-shell-panel px-3 py-2"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            {["open", "won", "lost", "closed"].map((value) => (
              <option key={value} value={value}>
                {resolveDealStatus(value, t)}
              </option>
            ))}
          </select>
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
          {pending ? "Сохранение..." : "Создать"}
        </button>
      </form>
    </div>
  );
}
