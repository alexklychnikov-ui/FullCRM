import Link from "next/link";
import { cookies } from "next/headers";

import { CrmNav } from "@/components/crm/CrmNav";
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

  const stageNames = new Map<string, string>();
  for (const pipeline of pipelines) {
    for (const stage of pipeline.stages) {
      stageNames.set(stage.id, stage.name);
    }
  }
  const companyNames = new Map(companies.map((company) => [company.id, company.name]));
  const contactNames = new Map(contacts.map((contact) => [contact.id, contact.full_name]));
  const assigneeNames = new Map(assignees.map((assignee) => [assignee.id, assignee.full_name]));

  return (
    <div>
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Сделки</h1>
          <p className="text-sm text-shell-muted">{deals.length} записей</p>
        </div>
        <Link
          className="rounded-md bg-shell-accent px-4 py-2 text-sm font-medium text-white"
          href="/crm/deals/new"
        >
          Новая сделка
        </Link>
      </div>
      <CrmNav active="deals" />
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
                    {deal.company_id ? companyNames.get(deal.company_id) : "—"}
                    {deal.contact_id ? ` · ${contactNames.get(deal.contact_id)}` : ""}
                  </p>
                </td>
                <td className="px-4 py-3 text-shell-muted">{stageNames.get(deal.stage_id) ?? "—"}</td>
                <td className="px-4 py-3 text-shell-muted">{deal.status}</td>
                <td className="px-4 py-3 text-shell-muted">
                  {deal.owner_user_id ? assigneeNames.get(deal.owner_user_id) ?? "—" : "—"}
                </td>
                <td className="px-4 py-3 text-shell-muted">
                  {deal.amount ? `${deal.amount} ${deal.currency}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
