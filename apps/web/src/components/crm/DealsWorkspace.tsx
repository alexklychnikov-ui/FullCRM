"use client";

import Link from "next/link";
import { useState } from "react";

import { DealStageLabel, DealStatusLabel } from "@/components/crm/DealLabels";
import { DealsPipelineBoard } from "@/components/crm/DealsPipelineBoard";
import type { Deal, PipelineStage } from "@/lib/api/crm";

type DealsWorkspaceProps = {
  deals: Deal[];
  stages: PipelineStage[];
  stageNames: Record<string, string>;
  companyNames: Record<string, string>;
  contactNames: Record<string, string>;
  assigneeNames: Record<string, string>;
};

type ViewMode = "board" | "list";

export function DealsWorkspace({
  deals,
  stages,
  stageNames,
  companyNames,
  contactNames,
  assigneeNames,
}: DealsWorkspaceProps) {
  const [view, setView] = useState<ViewMode>("board");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button
          className={`rounded-md px-3 py-1.5 text-sm ${
            view === "board"
              ? "bg-shell-accent text-white"
              : "bg-shell-panel text-shell-muted hover:text-white"
          }`}
          type="button"
          onClick={() => setView("board")}
        >
          Воронка
        </button>
        <button
          className={`rounded-md px-3 py-1.5 text-sm ${
            view === "list"
              ? "bg-shell-accent text-white"
              : "bg-shell-panel text-shell-muted hover:text-white"
          }`}
          type="button"
          onClick={() => setView("list")}
        >
          Список
        </button>
      </div>

      {view === "board" ? (
        <DealsPipelineBoard
          assigneeNames={assigneeNames}
          companyNames={companyNames}
          deals={deals}
          stages={stages}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-shell-border">
          <table className="min-w-full text-sm">
            <thead className="bg-shell-panel text-left text-shell-muted">
              <tr>
                <th className="px-4 py-3">Название</th>
                <th className="px-4 py-3">Этап</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3">Ответственный</th>
                <th className="px-4 py-3">Сумма</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((deal) => (
                <tr key={deal.id} className="border-t border-shell-border">
                  <td className="px-4 py-3">
                    <Link className="text-white hover:underline" href={`/crm/deals/${deal.id}`}>
                      {deal.title}
                    </Link>
                    <p className="text-xs text-shell-muted">
                      {deal.company_id ? companyNames[deal.company_id] : "—"}
                      {deal.contact_id ? ` · ${contactNames[deal.contact_id] ?? ""}` : ""}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-shell-muted">
                    <DealStageLabel stageName={stageNames[deal.stage_id]} />
                  </td>
                  <td className="px-4 py-3 text-shell-muted">
                    <DealStatusLabel status={deal.status} />
                  </td>
                  <td className="px-4 py-3 text-shell-muted">
                    {deal.owner_user_id ? assigneeNames[deal.owner_user_id] ?? "—" : "—"}
                  </td>
                  <td className="px-4 py-3 text-shell-muted">
                    {deal.amount ? `${deal.amount} ${deal.currency}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
