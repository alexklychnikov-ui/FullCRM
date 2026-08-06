import { cookies } from "next/headers";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CompanyDetailForm } from "@/components/crm/CompanyDetailForm";
import { CrmNav } from "@/components/crm/CrmNav";
import { EventTimeline } from "@/components/crm/EventTimeline";
import { ModuleDisabledState } from "@/components/modules/ModuleGate";
import { fetchCompany, fetchContacts, fetchDeals, fetchEventLogs, fetchPipelines } from "@/lib/api/crm";
import { getServerSession, hasModule } from "@/lib/auth/session";

type CompanyDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function CompanyDetailPage({ params }: CompanyDetailPageProps) {
  const { id } = await params;
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

  try {
    const [company, contacts, deals, pipelines, events] = await Promise.all([
      fetchCompany(id, cookieHeader),
      fetchContacts(cookieHeader),
      fetchDeals(cookieHeader),
      fetchPipelines(cookieHeader),
      fetchEventLogs({ entity_type: "company", entity_id: id }, cookieHeader),
    ]);

    const companyContacts = contacts.filter((c) => c.company_id === company.id);
    const companyDeals = deals
      .filter((deal) => deal.company_id === company.id)
      .sort((left, right) => right.updated_at.localeCompare(left.updated_at));

    const stageNames = new Map<string, string>();
    for (const pipeline of pipelines) {
      for (const stage of pipeline.stages) {
        stageNames.set(stage.id, stage.name);
      }
    }

    return (
      <div>
        <h1 className="mb-6 text-2xl font-semibold">{company.name}</h1>
        <CrmNav active="companies" />
        <CompanyDetailForm company={company} />
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">Контакты</h2>
          {companyContacts.length === 0 ? (
            <p className="text-sm text-shell-muted">Контактов пока нет.</p>
          ) : (
            <ul className="space-y-2">
              {companyContacts.map((contact) => (
                <li key={contact.id}>
                  <Link
                    className="text-white hover:underline"
                    href={`/crm/contacts/${contact.id}`}
                  >
                    {contact.full_name}
                  </Link>
                  {contact.email ? (
                    <span className="ml-2 text-sm text-shell-muted">{contact.email}</span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">Сделки</h2>
          {companyDeals.length === 0 ? (
            <p className="text-sm text-shell-muted">Сделок пока нет.</p>
          ) : (
            <ul className="space-y-2">
              {companyDeals.map((deal) => (
                <li key={deal.id}>
                  <Link className="text-white hover:underline" href={`/crm/deals/${deal.id}`}>
                    {deal.title}
                  </Link>
                  <span className="ml-2 text-sm text-shell-muted">
                    {deal.status}
                    {stageNames.get(deal.stage_id) ? ` · ${stageNames.get(deal.stage_id)}` : ""}
                    {deal.amount ? ` · ${deal.amount} ${deal.currency}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">События</h2>
          <EventTimeline events={events} />
        </section>
      </div>
    );
  } catch {
    notFound();
  }
}
