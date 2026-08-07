import Link from "next/link";
import { cookies } from "next/headers";

import { CrmNav } from "@/components/crm/CrmNav";
import { DealsWorkspace } from "@/components/crm/DealsWorkspace";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchAssignees, fetchCompanies, fetchContacts, fetchDeals, fetchPipelines } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

export default async function DealsPage() {
  const session = await getServerSession();

  if (!session) {
    return null;
  }

  if (!hasModule(session, "crm")) {
    return <ModuleDisabledState />;
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((item) => `${item.name}=${item.value}`)
    .join("; ");
  const [deals, pipelines, companies, contacts, assignees] = await Promise.all([
    fetchDeals(cookieHeader),
    fetchPipelines(cookieHeader),
    fetchCompanies(cookieHeader),
    fetchContacts(cookieHeader),
    fetchAssignees(cookieHeader),
  ]);

  const pipeline = pipelines.find((item) => item.is_default) ?? pipelines[0];
  const stages = pipeline?.stages ?? [];
  const boardDeals = pipeline
    ? deals.filter((deal) => deal.pipeline_id === pipeline.id)
    : deals;

  const stageNames = Object.fromEntries(
    pipelines.flatMap((item) => item.stages.map((stage) => [stage.id, stage.name])),
  );
  const companyNames = Object.fromEntries(companies.map((company) => [company.id, company.name]));
  const contactNames = Object.fromEntries(contacts.map((contact) => [contact.id, contact.full_name]));
  const assigneeNames = Object.fromEntries(
    assignees.map((assignee) => [assignee.id, assignee.full_name]),
  );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Сделки</h1>
          <p className="text-sm text-shell-muted">
            {boardDeals.length} записей
            {pipeline ? ` · ${pipeline.name}` : ""}
          </p>
        </div>
        <Link
          className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white"
          href="/crm/deals/new"
        >
          Новая сделка
        </Link>
      </div>
      <CrmNav active="deals" />
      <DealsWorkspace
        assigneeNames={assigneeNames}
        companyNames={companyNames}
        contactNames={contactNames}
        deals={boardDeals}
        stageNames={stageNames}
        stages={stages}
      />
    </div>
  );
}
