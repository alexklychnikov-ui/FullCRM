"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { Deal, PipelineStage } from "@/lib/api/crm";
import { transitionDeal } from "@/lib/api/crm";
import { useI18n } from "@/lib/i18n";
import { resolveDealStatus, resolveStageName } from "@/lib/i18n/labels";

type DealsPipelineBoardProps = {
  deals: Deal[];
  stages: PipelineStage[];
  companyNames: Record<string, string>;
  assigneeNames: Record<string, string>;
};

export function DealsPipelineBoard({
  deals: initialDeals,
  stages,
  companyNames,
  assigneeNames,
}: DealsPipelineBoardProps) {
  const { t } = useI18n();
  const orderedStages = useMemo(
    () => [...stages].sort((left, right) => left.position - right.position),
    [stages],
  );
  const [deals, setDeals] = useState(initialDeals);
  const [draggingDealId, setDraggingDealId] = useState<string | null>(null);
  const [dropStageId, setDropStageId] = useState<string | null>(null);
  const [pendingDealId, setPendingDealId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setDeals(initialDeals);
  }, [initialDeals]);

  const dealsByStage = useMemo(() => {
    const map = new Map<string, Deal[]>();
    for (const stage of orderedStages) {
      map.set(stage.id, []);
    }
    for (const deal of deals) {
      const bucket = map.get(deal.stage_id);
      if (bucket) {
        bucket.push(deal);
      }
    }
    return map;
  }, [deals, orderedStages]);

  async function moveDeal(dealId: string, targetStageId: string) {
    const current = deals.find((item) => item.id === dealId);
    if (!current || current.stage_id === targetStageId) {
      return;
    }

    const previousStageId = current.stage_id;
    setError("");
    setPendingDealId(dealId);
    setDeals((items) =>
      items.map((item) => (item.id === dealId ? { ...item, stage_id: targetStageId } : item)),
    );

    try {
      const updated = await transitionDeal(dealId, targetStageId);
      setDeals((items) => items.map((item) => (item.id === dealId ? updated : item)));
    } catch (moveError) {
      setDeals((items) =>
        items.map((item) =>
          item.id === dealId ? { ...item, stage_id: previousStageId } : item,
        ),
      );
      setError(
        moveError instanceof Error ? moveError.message : "Не удалось переместить сделку",
      );
    } finally {
      setPendingDealId(null);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-shell-muted">
        Перетащите карточку сделки в другую колонку, чтобы сменить этап воронки.
      </p>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <div className="flex gap-4 overflow-x-auto pb-2">
        {orderedStages.map((stage) => {
          const columnDeals = dealsByStage.get(stage.id) ?? [];
          const isActiveDrop = dropStageId === stage.id;

          return (
            <section
              key={stage.id}
              className={`flex w-80 shrink-0 flex-col rounded-lg border bg-shell-panel ${
                isActiveDrop ? "border-shell-accent" : "border-shell-border"
              }`}
              onDragLeave={() => {
                if (dropStageId === stage.id) {
                  setDropStageId(null);
                }
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setDropStageId(stage.id);
              }}
              onDrop={(event) => {
                event.preventDefault();
                const dealId = event.dataTransfer.getData("text/deal-id") || draggingDealId;
                setDropStageId(null);
                setDraggingDealId(null);
                if (dealId) {
                  void moveDeal(dealId, stage.id);
                }
              }}
            >
              <header className="border-b border-shell-border px-3 py-3">
                <div className="flex items-center justify-between gap-2">
                  <h2 className="text-sm font-medium text-white">
                    {resolveStageName(stage.name, t)}
                  </h2>
                  <span className="text-xs text-shell-muted">{columnDeals.length}</span>
                </div>
              </header>

              <ul className="min-h-40 flex-1 space-y-2 p-3">
                {columnDeals.length === 0 ? (
                  <li className="rounded-md border border-dashed border-shell-border px-3 py-6 text-center text-xs text-shell-muted">
                    Перетащите сюда
                  </li>
                ) : (
                  columnDeals.map((deal) => {
                    const isDragging = draggingDealId === deal.id;
                    const isPending = pendingDealId === deal.id;

                    return (
                      <li
                        key={deal.id}
                        draggable={!isPending}
                        className={`cursor-grab rounded-md border border-shell-border bg-shell-bg px-3 py-3 active:cursor-grabbing ${
                          isDragging ? "opacity-50" : ""
                        } ${isPending ? "opacity-60" : ""}`}
                        onDragEnd={() => {
                          setDraggingDealId(null);
                          setDropStageId(null);
                        }}
                        onDragStart={(event) => {
                          event.dataTransfer.setData("text/deal-id", deal.id);
                          event.dataTransfer.effectAllowed = "move";
                          setDraggingDealId(deal.id);
                        }}
                      >
                        <Link
                          className="block text-sm font-medium text-white hover:underline"
                          href={`/crm/deals/${deal.id}`}
                          onClick={(event) => {
                            if (draggingDealId) {
                              event.preventDefault();
                            }
                          }}
                        >
                          {deal.title}
                        </Link>
                        <p className="mt-1 text-xs text-shell-muted">
                          {deal.company_id ? companyNames[deal.company_id] ?? "—" : "—"}
                        </p>
                        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-shell-muted">
                          <span>{resolveDealStatus(deal.status, t)}</span>
                          {deal.amount ? (
                            <span>
                              {deal.amount} {deal.currency}
                            </span>
                          ) : null}
                          {deal.owner_user_id ? (
                            <span>{assigneeNames[deal.owner_user_id] ?? "—"}</span>
                          ) : null}
                        </div>
                      </li>
                    );
                  })
                )}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
