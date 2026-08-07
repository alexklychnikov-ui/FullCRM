"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createCommunicationMessage } from "@/lib/api/communications";

type CommunicationComposerProps = {
  contactId?: string | null;
  companyId?: string | null;
  dealId?: string | null;
};

export function CommunicationComposer({
  contactId = null,
  companyId = null,
  dealId = null,
}: CommunicationComposerProps) {
  const router = useRouter();
  const [body, setBody] = useState("");
  const [direction, setDirection] = useState<"outbound" | "inbound">("outbound");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = body.trim();
    if (!trimmed) {
      setError("Введите текст сообщения");
      return;
    }

    setPending(true);
    setError("");

    try {
      await createCommunicationMessage({
        channel_type: "email",
        direction,
        body: trimmed,
        contact_id: contactId,
        company_id: companyId,
        deal_id: dealId,
      });
      setBody("");
      router.refresh();
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Не удалось сохранить сообщение",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="mt-4 space-y-3 rounded-md border border-shell-border bg-shell-panel p-4" onSubmit={handleSubmit}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-white">Добавить сообщение (email)</p>
        <select
          className="rounded-md border border-shell-border bg-shell-bg px-2 py-1 text-sm"
          value={direction}
          onChange={(event) => setDirection(event.target.value as "outbound" | "inbound")}
        >
          <option value="outbound">Исходящее</option>
          <option value="inbound">Входящее</option>
        </select>
      </div>
      <p className="text-xs text-shell-muted">
        Ручная фиксация переписки в CRM. Письмо из почтового ящика не отправляется (Gmail — stub).
      </p>
      <textarea
        className="min-h-24 w-full rounded-md border border-shell-border bg-shell-bg px-3 py-2 text-sm"
        placeholder="Текст сообщения..."
        value={body}
        onChange={(event) => setBody(event.target.value)}
      />
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      <button
        className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        disabled={pending}
        type="submit"
      >
        {pending ? "Сохранение..." : "Сохранить в timeline"}
      </button>
    </form>
  );
}
